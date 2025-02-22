#
# This file sets up include directories, link directories, and
# compiler settings for a project to use DOLFIN. It should not be
# included directly, but rather through the DOLFIN_USE_FILE setting
# obtained from DOLFINConfig.cmake.
#

if (NOT DOLFIN_USE_FILE_INCLUDED)
  set(DOLFIN_USE_FILE_INCLUDED 1)

  if(POLICY CMP0012)
    cmake_policy(SET CMP0012 NEW)
  endif()

  # Require and use C++11
  set(CMAKE_CXX_STANDARD 11)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
  set(CMAKE_CXX_EXTENSIONS OFF)

  # Add DOLFIN-installed FindFoo.cmake files to path
  list(APPEND CMAKE_MODULE_PATH "/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/share/dolfin/cmake")

  # Check for Boost
  set(BOOST_ROOT $ENV{BOOST_DIR} $ENV{BOOST_HOME})
  if (BOOST_ROOT)
    set(Boost_NO_SYSTEM_PATHS on)
  endif()

  # Prevent FindBoost.cmake from looking for system Boost{foo}.cmake
  # files
  set(Boost_NO_BOOST_CMAKE true)

  set(Boost_USE_MULTITHREADED $ENV{BOOST_USE_MULTITHREADED})
  find_package(Boost 1.48 QUIET REQUIRED COMPONENTS
    timer)

  # Need to get VTK config because VTK uses advanced VTK features
  # which mean it's not enough to just link to the DOLFIN target. See
  # http://www.vtk.org/pipermail/vtk-developers/2013-October/014402.html
  if ()
    find_package(VTK HINTS ${VTK_DIR} $ENV{VTK_DIR} NO_MODULE QUIET)
    if (VTK_FOUND)
      include(${VTK_USE_FILE})
    endif()
  endif()

  if (TRUE)
    if (NOT PETSC::petsc)
      set(DOLFIN_SKIP_BUILD_TESTS TRUE)
      list(APPEND CMAKE_MODULE_PATH "/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/share/dolfin/cmake")
      find_package(PETSc REQUIRED QUIET)
      endif()
  endif()

  if (TRUE)
    if (NOT SLEPC::slepc)
      set(DOLFIN_SKIP_BUILD_TESTS TRUE)
      find_package(SLEPc REQUIRED QUIET)
    endif()
  endif()

  # Add compiler definitions needed to use DOLFIN
  add_definitions(${DOLFIN_CXX_DEFINITIONS})

  # Add compiler flags needed to use DOLFIN
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${DOLFIN_CXX_FLAGS}")
  set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${DOLFIN_LINK_FLAGS}")
  set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} ${DOLFIN_LINK_FLAGS}")
  set(CMAKE_MODULE_LINKER_FLAGS "${CMAKE_MODULE_LINKER_FLAGS} ${DOLFIN_LINK_FLAGS}")

  # Add include directories needed to use DOLFIN
  include_directories(${DOLFIN_INCLUDE_DIRS})
  include_directories(SYSTEM ${DOLFIN_3RD_PARTY_INCLUDE_DIRS})

endif()
