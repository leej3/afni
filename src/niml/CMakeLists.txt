cmake_minimum_required(VERSION 3.1...3.12)

# Packaging support
# set(CPACK_PACKAGE_VENDOR "Vendor name")
# set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Some summary")
# set(CPACK_PACKAGE_VERSION_MAJOR ${PROJECT_VERSION_MAJOR})
# set(CPACK_PACKAGE_VERSION_MINOR ${PROJECT_VERSION_MINOR})
# set(CPACK_PACKAGE_VERSION_PATCH ${PROJECT_VERSION_PATCH})
# # set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENCE")
# # set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/README.md")
# set(CPACK_SOURCE_GENERATOR "TGZ;ZIP")
# set(CPACK_SOURCE_IGNORE_FILES
#     /.git
#     /dist
#     /.*build.*
#     /\\\\.DS_Store
# )
# include(CPack)

# set(NIML_INCLUDE_DIRS "${CMAKE_CURRENT_SOURCE_DIR}" PARENT_SCOPE)

file(GLOB NIML_OBJS "niml_*")
list(REMOVE_ITEM NIML_OBJS "${CMAKE_CURRENT_SOURCE_DIR}/niml_fileread.c")


add_library(niml OBJECT ${NIML_OBJS})
target_include_directories(niml
    PUBLIC 
        $<INSTALL_INTERFACE:include>    
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
)
set_target_properties(niml PROPERTIES 
  PUBLIC_HEADER ../niml.h
  ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
  LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
  RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)
target_link_libraries(niml libheaders)
# install(TARGETS niml EXPORT nimlExport
#   RUNTIME DESTINATION "${CMAKE_INSTALL_PREFIX}" COMPONENT bin
#   LIBRARY DESTINATION "${CMAKE_INSTALL_PREFIX}" COMPONENT shlib
#   ARCHIVE DESTINATION "${CMAKE_INSTALL_PREFIX}"
#   PUBLIC_HEADER DESTINATION "${CMAKE_INSTALL_PREFIX}" COMPONENT include
#   )
# install(EXPORT nimlExport NAMESPACE niml::
#   DESTINATION ${CMAKE_INSTALL_PREFIX}
#   )

add_library(niml::niml ALIAS niml)

# export(EXPORT niml NAMESPACE niml:: FILE nimlTargets.cmake)
# export(PACKAGE niml)
# export(EXPORT jsonutils-targets FILE ${CMAKE_CURRENT_BINARY_DIR}/JSONUtilsTargets.cmake NAMESPACE JSONUtils::)

#Register package in user's package registry
# export(PACKAGE JSONUtils)