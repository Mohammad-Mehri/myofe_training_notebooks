"""This module contains the main part of Instant, the build_module function."""

# Copyright (C) 2008-2013 Kent-Andre Mardal
# Copyright (C) 2008-2013 Martin Sandve Alnes
# Copyright (C) 2009-2014 Johan Hake
# Copyright (C) 2009 Ilmar Wilbers
#
# This file is part of Instant.
#
# Instant is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Instant is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Instant. If not, see <http://www.gnu.org/licenses/>.
#
# Alternatively, Instant may be distributed under the terms of the BSD license.

import six
from six import string_types

import io, os, sys, shutil, glob, errno
from itertools import chain

# TODO: Import only the official interface
from .output import *
from .paths import *
from .signatures import *
from .cache import *
from .codegeneration import *
from .locking import file_lock


def assert_is_str(x):
    instant_assert(isinstance(x, string_types), "In instant.build_module: Expecting string.")


def assert_is_bool(x):
    instant_assert(isinstance(x, bool), "In instant.build_module: Expecting bool.")


def assert_is_str_list(x):
    instant_assert(isinstance(x, (list, tuple)), "In instant.build_module: Expecting sequence.")
    instant_assert(all(isinstance(i, string_types) for i in x), "In instant.build_module: Expecting sequence of strings.")


def strip_strings(x):
    assert_is_str_list(x)
    return [s.strip() for s in x]


def arg_strings(x):
    if isinstance(x, string_types):
        x = x.split()
    return strip_strings(x)


def makedirs(path):
    """
    Creates a directory (tree). If directory already excists it does nothing.
    """
    try:
        os.makedirs(path)
    except os.error as e:
        if e.errno != errno.EEXIST:
            raise


def copy_files(source, dest, files):
    """Copy a list of files from a source directory to a destination
    directory.  This may seem a bit complicated, but a lot of this
    code is error checking.

    """
    if os.path.exists(dest):
        overwriting = set(files) & set(glob.glob(os.path.join(dest, "*")))
        if overwriting:
            instant_warning("In instant.copy_files: Path '%s' already exists, "\
                "overwriting existing files: %r." % (dest, list(overwriting)))
    else:
        makedirs(dest)

    if source != dest:
        instant_debug("In instant.copy_files: Copying files %r from %r to %r"\
            % (files, source, dest))

        for f in files:
            a = os.path.join(source, f)
            b = os.path.join(dest, f)
            instant_assert(a != b, "In instant.copy_files: Seems like the "\
                "input files are absolute paths, should be relative to "\
                "source. (%r, %r)" % (a, b))
            instant_assert(os.path.isfile(a), "In instant.copy_files: "\
                "Missing source file '%s'." % a)
            if os.path.isfile(b):
                os.remove(b)
            shutil.copyfile(a, b)


def recompile(modulename, module_path, new_compilation_checksum,
              build_system="distutils"):
    """Recompile module if the new checksum is different from
    the one in the checksum file in the module directory."""

    assert(build_system in ["distutils", "cmake"])
    # Check if the old checksum matches the new one
    compilation_checksum_filename = "%s.checksum" % modulename
    if os.path.exists(compilation_checksum_filename):
        checksum_file = io.open(compilation_checksum_filename, encoding="utf8")
        old_compilation_checksum = checksum_file.readline()
        checksum_file.close()
        if old_compilation_checksum == new_compilation_checksum:
            return

    # Create log file for logging of compilation errors
    compile_log_filename = os.path.join(module_path, "compile.log")
    compile_log_filename_dest = os.path.join(get_default_error_dir(), \
                                             modulename, "compile.log")

    ret = 1
    try:
        compile_log_contents = None
        instant_info("--- Instant: compiling ---")

        # TODO: The three blocks below can be made a function and
        # three calls
        if build_system == "distutils":
            # Build extension module with distutils
            python_interp = sys.executable
            cmd = python_interp + " setup.py build_ext install --install-platlib=."
            instant_debug("cmd = %s" % cmd)
            ret, output = get_status_output(cmd)
            write_file(compile_log_filename, output)
            if ret != 0:
                compile_log_contents = output
                if os.path.exists(compilation_checksum_filename):
                    os.remove(compilation_checksum_filename)
                msg = "In instant.recompile: The module did not compile with command '%s', see '%s'"
                instant_error(msg % (cmd, compile_log_filename_dest))
        else:
            # Build makefile for extension module with cmake
            cmd = "cmake -DDEBUG=TRUE .";
            #cmd = "cmake .";
            instant_debug("cmd = %s" % cmd)
            ret, output = get_status_output(cmd)
            write_file(compile_log_filename, output)
            if ret != 0:
                compile_log_contents = output
                if os.path.exists(compilation_checksum_filename):
                    os.remove(compilation_checksum_filename)
                msg = "In instant.recompile: The module did not compile with command '%s', see '%s'"
                instant_error(msg % (cmd, compile_log_filename_dest))

            # Build extension module with cmake generated makefile
            cmd = "make VERBOSE=1"
            instant_debug("cmd = %s" % cmd)
            ret, output = get_status_output(cmd)
            write_file(compile_log_filename, output, mode="a")
            if ret != 0:
                compile_log_contents = output
                if os.path.exists(compilation_checksum_filename):
                    os.remove(compilation_checksum_filename)
                msg = "In instant.recompile: The module did not compile with command '%s', see '%s'"
                instant_error(msg % (cmd, compile_log_filename_dest))

    finally:
        if ret != 0:
            if "INSTANT_DISPLAY_COMPILE_LOG" in list(os.environ.keys()):
                instant_warning("")
                instant_warning("Content of instant compile.log")
                instant_warning("==============================")
                instant_warning(compile_log_contents)
                instant_warning("")

            # Copy module to error dir
            module_path = copy_to_cache(module_path, get_default_error_dir(),
                                        modulename,
                                        check_for_existing_path=False)

    # Compilation succeeded, write new_compilation_checksum to
    # checksum_file
    write_file(compilation_checksum_filename, new_compilation_checksum)


def copy_to_cache(module_path, cache_dir, modulename,
                  check_for_existing_path=True):
    "Copy module directory to cache."
    # Get lock, check if the module exists, _otherwise_ copy the
    # finished compiled module from /tmp/foo to the cache directory,
    # and then release lock
    with file_lock(cache_dir, modulename) as lock:

        # Validate the path
        cache_module_path = os.path.join(cache_dir, modulename)
        if check_for_existing_path and os.path.exists(os.path.join(\
            cache_module_path, "finished_copying")):
            # This indicates a race condition has happened (and is
            # being avoided!).
            instant_warning("In instant.build_module: Path '%s' already exists,"\
                " but module wasn't found in cache previously. Not overwriting,"\
                " assuming this module is valid." % cache_module_path)

            return cache_module_path

            # Not deleting anymore, relying on locking system
            #shutil.rmtree(cache_module_path, ignore_errors=True)

        # Error checks
        instant_assert(os.path.isdir(module_path), "In instant.build_module:"\
                       " Cannot copy non-existing directory %r!" % module_path)
        if check_for_existing_path and os.path.isdir(cache_module_path):
            instant_error("In instant.build_module: Cache directory %r shouldn't"\
                          " exist at this point!" % cache_module_path)
        instant_debug("In instant.build_module: Copying built module from %r"\
            " to cache at %r" % (module_path, cache_module_path))

        # Do the copying and mark that we are finished by creating an
        # empty file finished_copying
        try:
            shutil.copytree(module_path, cache_module_path)
            with io.open(os.path.join(cache_module_path, "finished_copying"),
                             "w", encoding="utf8") as dummy:
                pass            
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        finally:
            delete_temp_dir()

    return cache_module_path


def build_module(modulename=None, source_directory=".",
                 code="", init_code="",
                 additional_definitions="", additional_declarations="",
                 sources=[], wrap_headers=[],
                 local_headers=[], system_headers=[],
                 include_dirs=['.'], library_dirs=[], libraries=[],
                 swigargs=['-c++', '-fcompact', '-O', '-I.', '-small'],
                 swig_include_dirs = [],
                 cppargs=['-O2'], lddargs=[],
                 object_files=[], arrays=[],
                 generate_interface=True, generate_setup=True,
                 cmake_packages=[],
                 signature=None, cache_dir=None):
    """Generate and compile a module from C/C++ code using SWIG.

    Arguments:
    ==========
    The keyword arguments are as follows:
      - B{modulename}:
        - The name you want for the module.
          If specified, the module will not be cached.
          If missing, a name will be constructed based on
          a checksum of the other arguments, and the module
          will be placed in the global cache. String.
      - B{source_directory}:
        - The directory where user supplied files reside. The files
        given in B{sources}, B{wrap_headers}, and B{local_headers}
        are expected to exist in this directory. String.
      - B{code}:
        - A string containing C or C++ code to be compiled and wrapped. String.
      - B{init_code}:
        - Code that should be executed when the Instant module is
        imported. This code is inserted in the SWIG interface file, and is
        used for instance for calling C{import_array()} used for the
        initialization of NumPy arrays. String.
      - B{additional_definitions}:
        - Additional definitions (typically needed for inheritance)
        for interface file. These definitions should be given as triple-quoted
        strings in the case they span multiple lines, and are placed both in the
        initial block for C/C++ code (C{%{,%}}-block), and the main section
        of the interface file. String.
      - B{additional_declarations}:
        - Additional declarations (typically needed for inheritance)
        for interface file. These declarations should be given as triple-quoted
        strings in the case they span multiple lines, and are plaves in the main
        section of the interface file. String.
      - B{sources}:
        - Source files to compile and link with the module. These
        files are compiled togehter with the SWIG-generated wrapper file into
        the final library file. Should reside in directory specified in
        B{source_directory}. List of strings.
      - B{wrap_headers}:
        - Local header files that should be wrapped by SWIG. The
        files specified will be included both in the initial block for C/C++ code
        (with a C directive) and in the main section of the interface file (with
        a SWIG directive). Should reside in directory specified in
        B{source_directory}. List of strings.
      - B{local_headers}:
        - Local header files required to compile the wrapped
        code. The files specified will be included in the initial block for
        C/C++ code (with a C directive). Should reside in directory specified in
        B{source_directory}. List of strings.
      - B{system_headers}:
        - System header files required to compile the wrapped
        code. The files specified will be included in the initial block for C/C++
        code (with a C directive). List of strings.
      - B{include_dirs}:
        - Directories to search for header files for building the
        extension module. Needs to be absolute path names. List of strings.
      - B{library_dirs}:
        - Directories to search for libraries (C{-l}) for building
        the extension module. Needs to be absolute paths. List of strings.
      - B{libraries}:
        -  Libraries needed by the Instant module. The libraries will
        be linked in from the shared object file. The initial C{-l} is added
        automatically. List of strings.
      - B{swigargs}:
        - List of arguments to swig, e.g. C{["-lpointers.i"]}
          to include the SWIG pointers.i library.
      - B{swig_include_dirs}:
        - A list of directories to include in the 'swig' command.
      - B{cppargs}:
        - List of arguments to the compiler, e.g. C{["-Wall", "-fopenmp"]}.
      - B{lddargs}:
        - List of arguments to the linker, e.g. C{["-E", "-U"]}.
      - B{object_files}:
        - If you want to compile the files yourself. TODO: Not yet supported.
      - B{arrays}:
        - A nested list describing the C arrays to be made from NumPy arrays.
        The SWIG interface for fil NumPy is used. For 1D arrays, the inner
        list should contain strings with the variable names for the length of
        the arrays and the array itself. 2D matrices should contain the names
        of the dimensions in the two directions as well as the name of the
        array, and 3D tensors should contain the names of the dimensions in
        the three directions in addition to the name of the array.
        If the NumPy array har more than four dimensions, the inner list should
        contain strings with variable names for the number of dimensions,
        the length in each dimension as a pointer, and the array itself, respectively.
      - B{generate_interface}:
        - A bool to indicate if you want to generate the interface files.
      - B{generate_setup}:
        - A bool to indicate if you want to generate the setup.py file.
      - B{cmake_packages}:
        - A list with CMake configured packages which are used to configure
        and build the extension module. If used it will override the default
        behaviour of using distutils.
      - B{signature}:
        - A signature string to identify the form instead of the source code.
      - B{cache_dir}:
        - A directory to look for cached modules and place new ones.
          If missing, a default directory is used. Note that the module
          will not be cached if B{modulename} is specified.
          The cache directory should not be used for anything else.
    """

    # Store original directory to be able to restore later
    original_path = os.getcwd()

    # --- Validate arguments

    if sys.version_info[0] > 2:
        swigargs = swigargs + ['-py3']

    instant_assert(modulename is None or isinstance(modulename, string_types),
        "In instant.build_module: Expecting modulename to be string or None.")
    assert_is_str(source_directory)
    source_directory = os.path.abspath(source_directory)
    assert_is_str(code)
    assert_is_str(init_code)
    assert_is_str(additional_definitions)
    assert_is_str(additional_declarations)
    sources           = strip_strings(sources)
    wrap_headers      = strip_strings(wrap_headers)
    local_headers     = strip_strings(local_headers)
    system_headers    = strip_strings(system_headers)
    include_dirs      = strip_strings(include_dirs)
    library_dirs      = strip_strings(library_dirs)
    libraries         = strip_strings(libraries)
    swigargs          = arg_strings(swigargs)
    swig_include_dirs = strip_strings(swig_include_dirs)
    cppargs           = arg_strings(cppargs)
    lddargs           = arg_strings(lddargs)
    object_files      = strip_strings(object_files)
    arrays            = [strip_strings(a) for a in arrays]
    assert_is_bool(generate_interface)
    assert_is_bool(generate_setup)
    cmake_packages   = strip_strings(cmake_packages)

    instant_assert(signature is None \
                   or isinstance(signature, string_types) \
                   or hasattr(signature, "signature"), "In instant.build_module: Expecting modulename to be string or None.")

    instant_assert(not (signature is not None and modulename is not None), "In instant.build_module: Can't have both modulename and signature.")

    # --- Replace arguments with defaults if necessary

    cache_dir = validate_cache_dir(cache_dir)

    # Split sources by file-suffix (.c or .cpp)
    csrcs = [f for f in sources if f.endswith('.c') or f.endswith('.C')]
    cppsrcs = [f for f in sources if f.endswith('.cpp') or f.endswith('.cxx')]
    instant_assert(len(csrcs) + len(cppsrcs) == len(sources), "In instant.build_module: Source files must have '.c' or '.cpp' suffix")

    # --- Debugging code
    instant_debug('In instant.build_module:')
    instant_debug('::: Begin Arguments :::')
    instant_debug('    modulename: %r' % modulename)
    instant_debug('    source_directory: %r' % source_directory)
    instant_debug('    code: %r' % code)
    instant_debug('    init_code: %r' % init_code)
    instant_debug('    additional_definitions: %r' % additional_definitions)
    instant_debug('    additional_declarations: %r' % additional_declarations)
    instant_debug('    sources: %r' % sources)
    instant_debug('    csrcs: %r' % csrcs)
    instant_debug('    cppsrcs: %r' % cppsrcs)
    instant_debug('    wrap_headers: %r' % wrap_headers)
    instant_debug('    local_headers: %r' % local_headers)
    instant_debug('    system_headers: %r' % system_headers)
    instant_debug('    include_dirs: %r' % include_dirs)
    instant_debug('    library_dirs: %r' % library_dirs)
    instant_debug('    libraries: %r' % libraries)
    instant_debug('    swigargs: %r' % swigargs)
    instant_debug('    swig_include_dirs: %r' % swig_include_dirs)
    instant_debug('    cppargs: %r' % cppargs)
    instant_debug('    lddargs: %r' % lddargs)
    instant_debug('    object_files: %r' % object_files)
    instant_debug('    arrays: %r' % arrays)
    instant_debug('    generate_interface: %r' % generate_interface)
    instant_debug('    generate_setup: %r' % generate_setup)
    instant_debug('    cmake_packages: %r' % cmake_packages)
    instant_debug('    signature: %r' % signature)
    instant_debug('    cache_dir: %r' % cache_dir)
    instant_debug('::: End Arguments :::')

    # --- Setup module directory, making it and copying
    #     files to it if necessary, and compute a modulename
    #     if it isn't specified explicitly

    if modulename is None:
        # Compute a signature if we have none passed by the user:
        if signature is None:
            # Collect arguments used for checksum creation,
            # including everything that affects the interface
            # file generation and module compilation.
            checksum_args = ( \
                # We don't care about the modulename, that's what
                # we're trying to construct!
                #modulename,
                # We don't care where the user code resides:
                #source_directory,
                code, init_code,
                additional_definitions,
                additional_declarations,
                # Skipping filenames, since we use the file contents:
                #sources, wrap_headers,
                #local_headers,
                system_headers,
                include_dirs, library_dirs, libraries,
                swig_include_dirs, swigargs, cppargs, lddargs,
                object_files, arrays,
                generate_interface, generate_setup, cmake_packages,
                # The signature isn't defined, and the cache_dir
                # doesn't affect the module:
                #signature, cache_dir)
                sys.version
            )
            allfiles = sources + wrap_headers + local_headers
            allfiles = [os.path.join(source_directory, f) for f in allfiles]
            text = "\n".join((str(a) for a in checksum_args))
            signature = modulename_from_checksum(compute_checksum(text, allfiles))
            modulename = signature
            moduleids = [signature]
        else:
            module, moduleids = check_memory_cache(signature)
            if module: return module
            modulename = moduleids[-1]

        # Look for module in disk cache
        module = check_disk_cache(modulename, cache_dir, moduleids)
        if module: return module

        # Make a temporary module path for compilation
        module_path = os.path.join(get_temp_dir(), modulename)
        instant_assert(not os.path.exists(module_path), "In instant.build_module: Not expecting module_path to exist: '%s'"\
            % module_path)
        makedirs(module_path)
        use_cache = True
    else:
        use_cache = False
        moduleids = []
        module_path = os.path.join(original_path, modulename)
        makedirs(module_path)

        ## Look for module in memory cache
        #module, moduleids = check_memory_cache(modulename)
        #if module: return module
        #instant_assert(modulename == moduleids[-1] and len(moduleids) == 1, "Logic breach.")
        ## Look for module in local directory
        #module = check_disk_cache(modulename, original_path, moduleids)
        #if module: return module

    # Wrapping rest of code in try-block to
    # clean up at the end if something fails.
    try:
        # --- Copy user-supplied files to module path

        module_path = os.path.abspath(module_path)
        files_to_copy = sources + wrap_headers + local_headers + object_files
        copy_files(source_directory, module_path, files_to_copy)
        # At this point, all user input files should reside in module_path

        # --- Generate additional files in module directory
        os.chdir(module_path)

        # Generate __init__.py which imports compiled module contents
        write_file("__init__.py", "from __future__ import absolute_import\nfrom .%s import *" \
                    % modulename)

        # Generate SWIG interface if wanted
        ifile_name = "%s.i" % modulename
        if generate_interface:
            write_interfacefile(ifile_name, modulename, code, init_code,
                                additional_definitions,
                                additional_declarations, system_headers,
                                local_headers, wrap_headers, arrays)

        # Generate setup.py if wanted
        if generate_setup and not cmake_packages:
            setup_name = "setup.py"
            write_setup(setup_name, modulename, csrcs, cppsrcs, local_headers,
                        include_dirs, library_dirs, libraries,
                        swig_include_dirs, swigargs, cppargs, lddargs)
            build_system = "distutils"

        else:
            write_cmakefile(modulename, cmake_packages, csrcs, cppsrcs,
                            local_headers, include_dirs, library_dirs,
                            libraries, swig_include_dirs, swigargs, cppargs,
                            lddargs)
            build_system = "cmake"

        # --- Build module

        # At this point we have all the files, and can make the total
        # checksum from all file contents. This is used to decide
        # whether the module needs recompilation or not.

        # Compute new_compilation_checksum
        # Collect arguments used for checksum creation,
        # including everything that affects the module compilation.
        # Since the interface file is included in allfiles,
        # we don't need stuff that modifies it here.
        checksum_args = ( \
                         # We don't care about the modulename, that's what
                         # we're trying to construct!
                         #modulename,
                         # We don't care where the user code resides:
                         #source_directory,
                         #code, init_code,
                         #additional_definitions, additional_declarations,
                         # Skipping filenames, since we use the file contents:
                         #sources, wrap_headers,
                         #local_headers,
                         system_headers,
                         include_dirs, library_dirs, libraries,
                         swigargs, swig_include_dirs, cppargs, lddargs,
                         object_files, #arrays,
                         #generate_interface, generate_setup,
                         # The signature isn't defined, and the
                         # cache_dir doesn't affect the module:
                         #signature, cache_dir)
                         )
        text = "\n".join((str(a) for a in checksum_args))
        allfiles = sources + wrap_headers + local_headers + [ifile_name]
        new_compilation_checksum = compute_checksum(text, allfiles)

        # Recompile if necessary
        recompile(modulename, module_path, new_compilation_checksum,
                  build_system)

        # --- Load, cache, and return module

        # Copy compiled module to cache
        if use_cache:
            module_path = copy_to_cache(module_path, cache_dir, modulename)

        # Import module and place in memory cache
        module = import_and_cache_module(module_path, modulename, moduleids)

        if not module:
            instant_error("Failed to import newly compiled module!")

        instant_debug("In instant.build_module: Returning %s from build_module."\
            % module)

        return module
        # The end!

    finally:
        # Always get back to original directory.
        os.chdir(original_path)

    instant_error("In instant.build_module: Should never reach this point!")
    # end build_module


def build_module_vtk(c_code, cache_dir=None):
    original_path = os.getcwd()
    cache_dir = validate_cache_dir(cache_dir)
    signature = modulename_from_checksum(compute_checksum(c_code))
    modulename = signature
    moduleids = [signature]
    module_path = os.path.join(get_temp_dir(), modulename)

    makedirs(module_path)
    os.chdir(module_path)

    write_cmakefile(modulename)
    s = generate_interface_file_vtk(signature, c_code)
    write_vtk_interface_file(signature, c_code)

    ret, output = get_status_output("cmake -DDEBUG=TRUE . > cmake.log ")
    ret, output = get_status_output("make > compile.log ")

    module_path = copy_to_cache(module_path, cache_dir, modulename)

    os.chdir(original_path)

    module = import_and_cache_module(module_path, modulename, moduleids)

    return module


def build_module_vmtk(c_code, cache_dir=None):
    original_path = os.getcwd()
    cache_dir = validate_cache_dir(cache_dir)
    signature = modulename_from_checksum(compute_checksum(c_code))
    modulename = signature
    moduleids = [signature]
    module_path = os.path.join(get_temp_dir(), modulename)

    makedirs(module_path)
    os.chdir(module_path)

    write_vmtk_cmakefile(modulename)
    s = generate_interface_file_vtk(signature, c_code)
    write_vtk_interface_file(signature, c_code)

    ret, output = get_status_output("cmake -DDEBUG=TRUE . > cmake.log ")
    ret, output = get_status_output("make > compile.log ")

    module_path = copy_to_cache(module_path, cache_dir, modulename)

    os.chdir(original_path)

    module = import_and_cache_module(module_path, modulename, moduleids)

    return module
