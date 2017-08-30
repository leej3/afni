cmake_minimum_required(VERSION 2.6)
project(3DEdge)
set(3DEDGE_INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/src)
set(3DEDGE_INCLUDE_DIRS ${3DEDGE_INCLUDE_DIRS} PARENT_SCOPE)

add_subdirectory(src)

