# - Build details for DOLFIN: Dynamic Object-oriented Library for
# - FINite element computation
#
# This file has been automatically generated.

# FIXME: Check that naming conforms to CMake standards

if (POLICY CMP0011)
  cmake_policy(SET CMP0011 NEW)
endif()

if (POLICY CMP0012)
  cmake_policy(SET CMP0012 NEW)
endif()

# Compute path
get_filename_component(DOLFIN_CMAKE_DIR "${CMAKE_CURRENT_LIST_FILE}" PATH)

# Library dependencies (contains definitions for IMPORTED targets)
# NOTE: DOLFIN demo CMakeLists.txt are written to be stand-alone, as
# well as the build system building the demo. Therefore, we need the
# below guard to avoid exporting the targets twice.
if (NOT TARGET dolfin)
  include("${DOLFIN_CMAKE_DIR}/DOLFINTargets.cmake")
endif()

# Compilers
set(DOLFIN_CXX_COMPILER "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang++")

# Compiler defintions
set(DOLFIN_CXX_DEFINITIONS "-DDOLFIN_VERSION=\"2017.1.0\";-DNDEBUG;-DDOLFIN_SIZE_T=8;-DDOLFIN_LA_INDEX_SIZE=4;-DHAS_HDF5;-DHAS_SLEPC;-DHAS_PETSC;-DHAS_UMFPACK;-DHAS_CHOLMOD;-DHAS_SCOTCH;-DHAS_ZLIB;-DHAS_MPI")

# Compiler flags
set(DOLFIN_CXX_FLAGS "-std=c++11 -stdlib=libc++  -arch x86_64 -mmacosx-version-min=10.9 -stdlib=libc++ -m64  ")

# Linker flags
set(DOLFIN_LINK_FLAGS "-Wl,-rpath,/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/lib  -arch x86_64 -headerpad_max_install_names -mmacosx-version-min=10.9 -lc++ -L/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/lib ")

# Include directories
set(DOLFIN_INCLUDE_DIRS "/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include")

# Third party include directories
set(DOLFIN_3RD_PARTY_INCLUDE_DIRS "/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/lib/python2.7/site-packages/ffc/backends/ufc;/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include;/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include;/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include;/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include;/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include;/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include/eigen3;/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include;/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include")

# Python variables
if ("ON" AND "TRUE")
  if (NOT PYTHON_EXECUTABLE)
    set(PYTHON_EXECUTABLE /Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/bin/python)
  endif()
  # Find Python interpreter (defines PYTHON_VERSION)
  find_package(PythonInterp)

  set(DOLFIN_PYTHON_FILE
    "${DOLFIN_CMAKE_DIR}/DOLFINPython${PYTHON_VERSION_MAJOR}${PYTHON_VERSION_MINOR}.cmake")
  if (EXISTS "${DOLFIN_PYTHON_FILE}")
    include("${DOLFIN_PYTHON_FILE}")
  endif()
endif()

# SWIG executable
set(DOLFIN_SWIG_EXECUTABLE "/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/bin/swig")

# DOLFIN library
set(DOLFIN_LIBRARIES dolfin)

# Version
set(DOLFIN_VERSION_MAJOR "2017")
set(DOLFIN_VERSION_MINOR "1")
set(DOLFIN_VERSION_MICRO "0")
set(DOLFIN_VERSION_STR   "2017.1.0")

# The location of the UseDOLFIN.cmake file
set(DOLFIN_USE_FILE "${DOLFIN_CMAKE_DIR}/UseDOLFIN.cmake")
