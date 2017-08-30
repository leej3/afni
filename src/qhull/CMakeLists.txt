project(qhull)

file(GLOB QHULL_SRCS "*.c")
foreach(filename qhull unix qdelaun rbox)
  list(REMOVE_ITEM QHULL_SRCS "${CMAKE_CURRENT_SOURCE_DIR}/${filename}.c")
endforeach(filename)

add_library(qhull_srcs OBJECT ${QHULL_SRCS})

set(QHULL_BINARIES unix qdelaun rbox)
foreach(target ${QHULL_BINARIES})
  add_executable(${target} ${target}.c $<TARGET_OBJECTS:qhull_srcs>)
  target_link_libraries(${target} m)
endforeach(target)

install(TARGETS ${QHULL_BINARIES}
       RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
       LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
       ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
       PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
) 

