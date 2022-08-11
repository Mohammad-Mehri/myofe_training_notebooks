"""This module contains helper functions for code generation."""

# Copyright (C) 2010, 2013 Kent-Andre Mardal
# Copyright (C) 2008 Martin Sandve Alnes
# Copyright (C) 2009 Ilmar Wilbers
# Copyright (C) 2013 Garth N. Wells
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

import sys
import re, os, io
from .output import instant_assert, instant_warning, instant_debug, write_file
from .config import get_swig_binary

def mapstrings(format, sequence):
    return "\n".join(format % i for i in sequence)

def reindent(code):
    '''Reindent a multiline string to allow easier to read syntax.

    Each line will be indented relative to the first non-empty line.
    Start the first line without text like shown in this example::

        code = reindent("""
            Foo
            Bar
                Blatti
            Ping
            """)

    makes all indentation relative to Foo.
    '''
    lines = code.split("\n")
    space = ""
    # Get initial spaces from first non-empty line:
    for l in lines:
        if l:
            r = re.search(r"^( [ ]*)", l)
            if r is not None:
                space = r.groups()[0]
            break
    if not space:
        return code
    n = len(space)
    instant_assert(space == " "*n, "Logic breach in reindent.")
    return "\n".join(re.sub(r"^%s" % space, "", l) for l in lines)

def write_interfacefile(filename, modulename, code, init_code,
                        additional_definitions, additional_declarations,
                        system_headers, local_headers, wrap_headers, arrays):
    """Generate a SWIG interface file. Intended for internal library use.

    The input arguments are as follows:
      - modulename (Name of the module)
      - code (Code to be wrapped)
      - init_code (Code to put in the init section of the interface file)
      - additional_definitions (Definitions to be placed in initial block with
        C code as well as in the main section of the SWIG interface file)
      - additional_declarations (Declarations to be placed in the main section
        of the SWIG interface file)
      - system_headers (A list of system headers with declarations needed by the wrapped code)
      - local_headers (A list of local headers with declarations needed by the wrapped code)
      - wrap_headers (A list of local headers that will be included in the code and wrapped by SWIG)
      - arrays (A nested list, the inner lists describing the different arrays)

    The result of this function is that a SWIG interface with
    the name modulename.i is written to the current directory.
    """
    instant_debug("Generating SWIG interface file '%s'." % filename)

    # create typemaps
    typemaps = ""
    valid_types = ['float', 'double', 'short', 'int', 'long', 'long long',
                   'unsigned short', 'unsigned int', 'unsigned long',
                   'unsigned long long']
    for a in arrays:
        if isinstance(a, tuple):
            a = list(a)
        DATA_TYPE = 'double'
        for vt in valid_types:
            if vt in a:
                DATA_TYPE = vt
                a.remove(vt)
        if 'in' in a:
            # input arrays
            a.remove('in')
            instant_assert(len(a) > 1 and len(a) < 5,
                           "Wrong number of elements in input array")
            if len(a) == 2:
                # 1-dimensional arrays, i.e. vectors
                typemaps += reindent("""
                %%apply (int DIM1, %(dtype)s* IN_ARRAY1) {(int %(n1)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'array' : a[1], 'dtype' : DATA_TYPE })
            elif len(a) == 3:
                # 2-dimensional arrays, i.e. matrices
                typemaps += reindent("""
                %%apply (int DIM1, int DIM2, %(dtype)s* IN_ARRAY2) {(int %(n1)s, int %(n2)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'n2' : a[1], 'array' : a[2], 'dtype' : DATA_TYPE })
            else:
                # 3-dimensional arrays, i.e. tensors
                typemaps += reindent("""
                %%apply (int DIM1, int DIM2, int DIM3, %(dtype)s* IN_ARRAY3) {(int %(n1)s, int %(n2)s, int %(n3)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'n2' : a[1], 'n3' : a[2], 'array' : a[3], 'dtype' : DATA_TYPE })
        elif 'out' in a:
            # output arrays
            a.remove('out')
            instant_assert(len(a) == 2, "Output array must be 1-dimensional")
            # 1-dimensional arrays, i.e. vectors
            typemaps += reindent("""
            %%apply (int DIM1, %(dtype)s* ARGOUT_ARRAY1) {(int %(n1)s, %(dtype)s* %(array)s)};
            """ % { 'n1' : a[0], 'array' : a[1], 'dtype' : DATA_TYPE })
        else:
            # in-place arrays
            instant_assert(len(a) > 1 and len(a) < 5,
                           "Wrong number of elements in output array")
            if 'multi' in a:
                # n-dimensional arrays, i.e. tensors > 3-dimensional
                a.remove('multi')
                typemaps += reindent("""
                %%typemap(in) (int %(n)s,int* %(ptv)s,%(dtype)s* %(array)s){
                  if (!PyArray_Check($input)) {
                    PyErr_SetString(PyExc_TypeError, "Not a NumPy array");
                    return NULL; ;
                  }
                  PyArrayObject* pyarray;
                  pyarray = (PyArrayObject*)$input;
                  $1 = int(pyarray->nd);
                  int* dims = new int[$1];
                  for (int d=0; d<$1; d++) {
                     dims[d] = int(pyarray->dimensions[d]);
                  }

                  $2 = dims;
                  $3 = (%(dtype)s*)pyarray->data;
                }
                %%typemap(freearg) (int %(n)s,int* %(ptv)s,%(dtype)s* %(array)s){
                    // deleting dims
                    delete $2;
                }
                """ % { 'n' : a[0] , 'ptv' : a[1], 'array' : a[2], 'dtype' : DATA_TYPE })
            elif len(a) == 2:
                # 1-dimensional arrays, i.e. vectors
                typemaps += reindent("""
                %%apply (int DIM1, %(dtype)s* INPLACE_ARRAY1) {(int %(n1)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'array' : a[1], 'dtype' : DATA_TYPE })
            elif len(a) == 3:
                # 2-dimensional arrays, i.e. matrices
                typemaps += reindent("""
                %%apply (int DIM1, int DIM2, %(dtype)s* INPLACE_ARRAY2) {(int %(n1)s, int %(n2)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'n2' : a[1], 'array' : a[2], 'dtype' : DATA_TYPE })
            else:
                # 3-dimensional arrays, i.e. tensors
                typemaps += reindent("""
                %%apply (int DIM1, int DIM2, int DIM3, %(dtype)s* INPLACE_ARRAY3) {(int %(n1)s, int %(n2)s, int %(n3)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'n2' : a[1], 'n3' : a[2], 'array' : a[3], 'dtype' : DATA_TYPE})
            # end
        # end if
    # end for

    system_headers_code = mapstrings('#include <%s>', system_headers)
    local_headers_code  = mapstrings('#include "%s"', local_headers)
    wrap_headers_code1  = mapstrings('#include "%s"', wrap_headers)
    wrap_headers_code2  = mapstrings('%%include "%s"', wrap_headers)

    numpy_i_include = ''
    if arrays:
        numpy_i_include = r'%include "numpy.i"'

    # Do not reindent as SWIG interface code can also include Python code.
    interface_string = """%%module  %(modulename)s
//%%module (directors="1") %(modulename)s

//%%feature("director");

%%{
#include <iostream>
%(additional_definitions)s
%(system_headers_code)s
%(local_headers_code)s
%(wrap_headers_code1)s
%(code)s
%%}

//%%feature("autodoc", "1");
%(numpy_i_include)s

%%init%%{
%(init_code)s
%%}

%(additional_definitions)s
%(additional_declarations)s
%(wrap_headers_code2)s
//%(typemaps)s
%(code)s;

""" % locals()

    write_file(filename, interface_string)
    instant_debug("Done generating interface file.")

def write_setup(filename, modulename, csrcs, cppsrcs, local_headers, include_dirs, library_dirs, libraries, swig_include_dirs, swigargs, cppargs, lddargs):
    """Generate a setup.py file. Intended for internal library use."""
    instant_debug("Generating %s." % filename)

    swig_include_dirs.append(os.path.join(os.path.dirname(__file__), 'swig'))

    # Handle arguments
    swigfilename = "%s.i" % modulename
    wrapperfilename = "%s_wrap.cxx" % modulename

    # Treat C and C++ files in the same way for now
    cppsrcs = cppsrcs + csrcs + [wrapperfilename]

    swig_args = ""
    if swigargs:
        swig_args = " ".join(swigargs)

    compile_args = ""
    if cppargs:
        compile_args = ", extra_compile_args=%r" % cppargs

    link_args = ""
    if lddargs:
        link_args = ", extra_link_args=%r" % lddargs

    swig_include_dirs = " ".join("-I%s"%d for d in swig_include_dirs)
    if len(local_headers) > 0:
        swig_include_dirs += " -I.."

    py3 = "" if sys.version_info[0] < 3 else "-py3"

    # Generate code
    code = reindent("""
        import os
        from distutils.core import setup, Extension
        name = '%s'
        swig_cmd =r'%s -python %s %s %s %s'
        os.system(swig_cmd)
        sources = %s
        setup(name = '%s',
              ext_modules = [Extension('_' + '%s',
                             sources,
                             include_dirs=%s,
                             library_dirs=%s,
                             libraries=%s %s %s)])
        """ % (modulename, get_swig_binary(), py3, swig_include_dirs, swig_args, \
               swigfilename, cppsrcs, modulename, modulename, include_dirs, \
               library_dirs, libraries, compile_args, link_args))

    write_file(filename, code)
    instant_debug("Done writing setup.py file.")


def _test_write_interfacefile():
    modulename = "testmodule"
    code = "void foo() {}"
    init_code = "/* custom init code */"
    additional_definitions = "/* custom definitions */"
    additional_declarations = "/* custom declarations */"
    system_headers = ["system_header1.h", "system_header2.h"]
    local_headers = ["local_header1.h", "local_header2.h"]
    wrap_headers = ["wrap_header1.h", "wrap_header2.h"]
    arrays = [["length1", "array1"], ["dims", "lengths", "array2"]]

    write_interfacefile("%s.i" % modulename, modulename, code, init_code, \
                        additional_definitions, additional_declarations, \
                        system_headers, local_headers, wrap_headers, arrays)
    print("".join(io.open("%s.i" % modulename, encoding="utf8").readlines()))

def _test_write_setup():
    modulename = "testmodule"
    csrcs = ["csrc1.c", "csrc2.c"]
    cppsrcs = ["cppsrc1.cpp", "cppsrc2.cpp"]
    local_headers = ["local_header1.h", "local_header2.h"]
    include_dirs = ["includedir1", "includedir2"]
    library_dirs = ["librarydir1", "librarydir2"]
    libraries = ["lib1", "lib2"]
    swig_include_dirs = ["swigdir1", "swigdir2"],
    swigargs = ["-Swigarg1", "-Swigarg2"]
    cppargs = ["-cpparg1", "-cpparg2"]
    lddargs = ["-Lddarg1", "-Lddarg2"]

    write_setup("setup.py", modulename, csrcs, cppsrcs, local_headers, \
                include_dirs, library_dirs, libraries, swig_include_dirs, \
                swigargs, cppargs, lddargs)
    print("".join(io.open("setup.py", encoding="utf8").readlines()))

def unique(sequence):
    return list(set(sequence))


def find_vtk_classes(str):
    pattern = "vtk\w*"
    l = unique(re.findall(pattern, str))
    return l

def create_typemaps(classes):
    s = ""

    typemap_template = """
%%typemap(in) %(class_name)s * {
    vtkObjectBase* obj = vtkPythonGetPointerFromObject($input, "%(class_name)s");
    %(class_name)s * oobj = NULL;
    if (obj->IsA("%(class_name)s")) {
        oobj = %(class_name)s::SafeDownCast(obj);
        $1 = oobj;
    }
}

%%typemap(out) %(class_name)s * {
   $result = vtkPythonGetObjectFromPointer($1);
}

   """

    for cl in classes:
        s += typemap_template % { "class_name" : cl }

    return s


def generate_vtk_includes(classes):
    s = """
#include "vtkPythonUtil.h"
    """
    for cl in classes:
        s += """
#include \"%s.h\" """ % cl
    return s


def generate_interface_file_vtk(signature, code):

    interface_template =  """
%%module test
%%{

%(includes)s

%(code)s

%%}

%(typemaps)s

%(code)s

"""
    class_list = find_vtk_classes(code)
    includes = generate_vtk_includes(class_list)
    typemaps = create_typemaps(class_list)
    s = interface_template % { "typemaps" : typemaps, "code" : code, "includes" : includes }
    return s

def write_cmakefile(module_name, cmake_packages, csrcs, cppsrcs, local_headers, include_dirs, library_dirs, libraries, swig_include_dirs, swigargs, cppargs, lddargs):

    find_package_template = """
# Configuration for package %(package)s
FIND_PACKAGE(%(package)s REQUIRED)
IF(%(package)s_FOUND)
 INCLUDE(${%(PACKAGE)s_USE_FILE})
ENDIF(%(package)s_FOUND)
"""

    cmake_form = dict(module_name=module_name)

    cmake_form["python_executable"] = sys.executable

    cmake_form["extra_libraries"] = ";".join(libraries)
    cmake_form["extra_include_dirs"] = ";".join(include_dirs)
    cmake_form["extra_library_dirs"] = ";".join(library_dirs)
    cmake_form["extra_swig_include_dirs"] = " -I".join([" "] + swig_include_dirs)

    cmake_form["extra_swigargs"] = " ".join(swigargs)

    cmake_form["swig_executable"] =  "\n".join(\
        """if (DEFINED %(package)s_SWIG_EXECUTABLE)
  set(SWIG_EXECUTABLE ${%(package)s_SWIG_EXECUTABLE})
endif()
""" % dict(package=package.upper()) for package in cmake_packages)


    cmake_form["find_packages"] = "\n\n".join(find_package_template % \
                                              dict(package=package,
                                                   PACKAGE=package.upper())\
                                              for package in cmake_packages)
    cmake_form["packages_definitions"] = "\n".join(
        "${%s_CXX_DEFINITIONS}" % package.upper()
        for package in cmake_packages)

    cmake_form["packages_definitions"] += "\n"+"\n".join(
        "${%s_PYTHON_DEFINITIONS}" % package.upper()
        for package in cmake_packages)

    cmake_form["package_include_dirs"] = "\n".join(\
        "include_directories(${%(package)s_PYTHON_INCLUDE_DIRS} ${%(package)s_3RD_PARTY_INCLUDE_DIRS} ${${NAME}_SOURCE_DIR})" %
        dict(package=package.upper()) for package in cmake_packages)

    cmake_form["package_flags"] = "\n".join(\
        """set(CMAKE_EXE_LINKER_FLAGS \"${CMAKE_EXE_LINKER_FLAGS} ${%(package)s_LINK_FLAGS}\")
set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} ${%(package)s_LINK_FLAGS}\")
""" %
        dict(package=package.upper()) for package in cmake_packages)

    cmake_form["package_swig_link_libraries"] = "\n".join(\
        """if (DEFINED %(package)s_LIBRARIES OR DEFINED %(package)s_3RD_PARTY_LIBRARIES OR DEFINED %(package)s_PYTHON_LIBRARIES)
  swig_link_libraries(${SWIG_MODULE_NAME} ${%(package)s_LIBRARIES} ${%(package)s_3RD_PARTY_LIBRARIES} ${%(package)s_PYTHON_LIBRARIES} ${EXTRA_SOURCE_LIB})
endif()""" %
        dict(package=package.upper()) for package in cmake_packages)

    cmake_form["package_python_definitions"] = "\n".join(\
        """if (DEFINED %(package)s_PYTHON_DEFINITIONS)
  add_definitions(${%(package)s_PYTHON_DEFINITIONS})
endif()""" %
        dict(package=package.upper()) for package in cmake_packages)

    cppsrcs.extend(csrcs)
    if len(cppsrcs) > 0:
        cmake_form["extra_sources_files"] = "set(SOURCE_FILES %s) " %  " ".join(cppsrcs)
    else:
        cmake_form["extra_sources_files"] = "set(SOURCE_FILES)"

    if cppargs:
        cmake_form["cppargs"] = "set(CMAKE_CXX_FLAGS \"${CMAKE_CXX_FLAGS} %s\")" % \
                                (" ".join(cppargs))
    else:
        cmake_form["cppargs"] = ""

    if lddargs:
        cmake_form["lddargs"] = "set(CMAKE_EXE_LINKER_FLAGS \""\
                                "${CMAKE_EXE_LINKER_FLAGS} %s\")" % (" ".join(lddargs))
    else:
        cmake_form["lddargs"] = ""

    cmake_template = """
cmake_minimum_required(VERSION 2.6.0)

set (NAME %(module_name)s)

PROJECT(${NAME})

set(PYTHON_EXECUTABLE %(python_executable)s)

%(find_packages)s

%(cppargs)s
%(lddargs)s

%(swig_executable)s

find_package(SWIG REQUIRED)
include(${SWIG_USE_FILE})

set(SWIG_MODULE_NAME ${NAME})
set(CMAKE_SWIG_FLAGS
  -module ${SWIG_MODULE_NAME}
  -shadow
  -modern
  -modernargs
  -fastdispatch
  -fvirtual
  -nosafecstrings
  -noproxydel
  -fastproxy
  -fastinit
  -fastunpack
  -fastquery
  -nobuildnone
%(packages_definitions)s
%(extra_swigargs)s
%(extra_swig_include_dirs)s
  )

set(CMAKE_SWIG_OUTDIR ${CMAKE_CURRENT_BINARY_DIR})

set(SWIG_SOURCES ${NAME}.i)

set_source_files_properties(${SWIG_SOURCES} PROPERTIES CPLUSPLUS ON)

set(EXTRA_INCLUDE_DIRS \"%(extra_include_dirs)s\")
if(EXTRA_INCLUDE_DIRS)
  include_directories(${EXTRA_INCLUDE_DIRS})
endif()
%(package_include_dirs)s

%(package_flags)s

set(EXTRA_LIBRARY_DIRS \"%(extra_library_dirs)s\")
if(EXTRA_LIBRARY_DIRS)
  link_directories(${EXTRA_LIBRARY_DIRS})
endif()

%(extra_sources_files)s

%(package_python_definitions)s

# Work-around for bug in CMake 3.0.0 (see
# http://www.cmake.org/Bug/view.php?id=14990)
set(SWIG_MODULE_NAME_ORIG "${SWIG_MODULE_NAME}")
if (${CMAKE_VERSION} MATCHES "3.0.0")
  set(SWIG_MODULE_NAME "_${SWIG_MODULE_NAME}")
endif()

swig_add_module(${SWIG_MODULE_NAME} python ${SWIG_SOURCES})

set(EXTRA_LIBRARIES %(extra_libraries)s)
if(SOURCE_FILES)
  set(CMAKE_CXX_FLAGS \"${CMAKE_CXX_FLAGS} -fpic\")
  add_library(source_file_lib
    STATIC
    ${SOURCE_FILES})
  set(EXTRA_LIBRARIES \"source_file_lib;${EXTRA_LIBRARIES}\")
endif()

if(EXTRA_LIBRARIES)
  string(STRIP \"${EXTRA_LIBRARIES}\" EXTRA_LIBRARIES)
  swig_link_libraries(${SWIG_MODULE_NAME} ${EXTRA_LIBRARIES})
endif()

%(package_swig_link_libraries)s

""" % cmake_form

    filename = "CMakeLists.txt"
    write_file(filename, cmake_template)

def write_itk_cmakefile(name):
    file_template = """
cmake_minimum_required(VERSION 2.6.0)

# This project is designed to be built outside the Insight source tree.
PROJECT(%(name)%s)

# Find ITK.
FIND_PACKAGE(ITK REQUIRED)
IF(ITK_FOUND)
  INCLUDE(${ITK_USE_FILE})
ENDIF(ITK_FOUND)

# Find VTK.
FIND_PACKAGE(VTK REQUIRED)
IF(VTK_FOUND)
  INCLUDE(${VTK_USE_FILE})
ENDIF(VTK_FOUND)

find_package(SWIG REQUIRED)
include(${SWIG_USE_FILE})

set(SWIG_MODULE_NAME %(name)s)
set(CMAKE_SWIG_FLAGS
  -module ${SWIG_MODULE_NAME}
  -shadow
  -modern
  -modernargs
  -fastdispatch
  -fvirtual
  -nosafecstrings
  -noproxydel
  -fastproxy
  -fastinit
  -fastunpack
  -fastquery
  -nobuildnone
  -Iinclude/swig
  )

set(CMAKE_SWIG_OUTDIR ${CMAKE_CURRENT_BINARY_DIR})

set(SWIG_SOURCES %(name)s.i)

set_source_files_properties(${SWIG_SOURCES} PROPERTIES CPLUSPLUS ON)

include_directories(${PYTHON_INCLUDE_PATH} ${%(name)s_SOURCE_DIR})

set(VTK_LIBS ITKCommon vtkCommon vtkImaging vtkIO vtkFiltering vtkRendering vtkGraphics vtkCommonPythonD vtkFilteringPythonD)

# Work-around for bug in CMake 3.0.0 (see
# http://www.cmake.org/Bug/view.php?id=14990)
set(SWIG_MODULE_NAME_ORIG "${SWIG_MODULE_NAME}")
if (${CMAKE_VERSION} MATCHES "3.0.0")
  set(SWIG_MODULE_NAME "_${SWIG_MODULE_NAME}")
endif()

swig_add_module(${SWIG_MODULE_NAME} python ${SWIG_SOURCES})

swig_link_libraries(${SWIG_MODULE_NAME} ${PYTHON_LIBRARIES} ${VTK_LIBS})


    """ % { "name" : name }

    with io.open("CMakeLists.txt", 'w', encoding="utf8") as f:
        f.write(file_template)


def write_vmtk_cmakefile(name):
    file_template = """
cmake_minimum_required(VERSION 2.6.0)

# This project is designed to be built outside the Insight source tree.
PROJECT(%(name)%s)

# Find ITK.
FIND_PACKAGE(ITK REQUIRED)
IF(ITK_FOUND)
  INCLUDE(${ITK_USE_FILE})
ENDIF(ITK_FOUND)

# Find VTK.
FIND_PACKAGE(VTK REQUIRED)
IF(VTK_FOUND)
  INCLUDE(${VTK_USE_FILE})
ENDIF(VTK_FOUND)

# Find VMTK.
#FIND_PACKAGE(VMTK REQUIRED)
#IF(VMTK_FOUND)
#  INCLUDE(${VMTK_USE_FILE})
#ENDIF(ITK_FOUND)

find_package(SWIG REQUIRED)
include(${SWIG_USE_FILE})

set(SWIG_MODULE_NAME %(name)s)
set(CMAKE_SWIG_FLAGS
  -module ${SWIG_MODULE_NAME}
  -shadow
  -modern
  -modernargs
  -fastdispatch
  -fvirtual
  -nosafecstrings
  -noproxydel
  -fastproxy
  -fastinit
  -fastunpack
  -fastquery
  -nobuildnone
  -Iinclude/swig
  )

set(CMAKE_SWIG_OUTDIR ${CMAKE_CURRENT_BINARY_DIR})

set(SWIG_SOURCES %(name)s.i)

set_source_files_properties(${SWIG_SOURCES} PROPERTIES CPLUSPLUS ON)

include_directories(${PYTHON_INCLUDE_PATH} ${%(name)s_SOURCE_DIR} /usr/local/include/vmtk)
link_directories(/usr/local/lib/vmtk .)

set(VTK_LIBS ITKCommon vtkCommon vtkImaging vtkIO vtkFiltering vtkRendering vtkGraphics vtkCommonPythonD vtkFilteringPythonD)
set(VMTK_LIBS vtkvmtkCommonPythonD vtkvmtkITKPythonD vtkvmtkCommon vtkvmtkITK vtkvmtkComputationalGeometryPythonD vtkvmtkMiscPythonD vtkvmtkComputationalGeometry vtkvmtkMisc vtkvmtkDifferentialGeometryPythonD vtkvmtkSegmentationPythonD vtkvmtkDifferentialGeometry vtkvmtkSegmentation vtkvmtkIOPythonD)

# Work-around for bug in CMake 3.0.0 (see
# http://www.cmake.org/Bug/view.php?id=14990)
set(SWIG_MODULE_NAME_ORIG "${SWIG_MODULE_NAME}")
if (${CMAKE_VERSION} MATCHES "3.0.0")
  set(SWIG_MODULE_NAME "_${SWIG_MODULE_NAME}")
endif()

swig_add_module(${SWIG_MODULE_NAME} python ${SWIG_SOURCES})

swig_link_libraries(${SWIG_MODULE_NAME} ${PYTHON_LIBRARIES} ${VTK_LIBS} ${VMTK_LIBS})


    """ % { "name" : name }

    with io.open("CMakeLists.txt", 'w', encoding="utf8") as f:
        f.write(file_template)


def write_vtk_interface_file(signature, code):
    filename = signature
    ifile = filename + ".i"
    ifile_code = generate_interface_file_vtk(signature, code)
    with io.open(ifile, 'w', encoding="utf8") as iff:
        iff.write(ifile_code)


if __name__ == "__main__":
    _test_write_interfacefile()
    print("\n"*3)
    _test_write_setup()
