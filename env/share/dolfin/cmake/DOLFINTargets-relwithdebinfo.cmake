#----------------------------------------------------------------
# Generated CMake target import file for configuration "RelWithDebInfo".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "dolfin" for configuration "RelWithDebInfo"
set_property(TARGET dolfin APPEND PROPERTY IMPORTED_CONFIGURATIONS RELWITHDEBINFO)
set_target_properties(dolfin PROPERTIES
  IMPORTED_LOCATION_RELWITHDEBINFO "${_IMPORT_PREFIX}/lib/libdolfin.2017.1.0.dylib"
  IMPORTED_SONAME_RELWITHDEBINFO "@rpath/libdolfin.2017.1.dylib"
  )

list(APPEND _IMPORT_CHECK_TARGETS dolfin )
list(APPEND _IMPORT_CHECK_FILES_FOR_dolfin "${_IMPORT_PREFIX}/lib/libdolfin.2017.1.0.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
