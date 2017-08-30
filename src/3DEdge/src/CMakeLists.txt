set(3DEDGE_SRCS 3dedge.c convert.c iopnm.c recline.c
 convert.h iopnm.h recline.h typedefs.h connexe.c extrema.c recbuffer.c
 zcross.c connexe.h extrema.h recbuffer.h
 zcross.h)
# currently not included: test-hyster-pnm.c test-edges-pnm.c test-edges.c

add_library(3DEdge ${3DEDGE_SRCS})

# todo: need to change these to target generator expressions
target_include_directories(3DEdge 
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
  PRIVATE 
    $<TARGET_PROPERTY:rickr,INTERFACE_INCLUDE_DIRECTORIES>)
 
target_link_libraries(3DEdge nifti2 nifticdf)
install(TARGETS 3DEdge
       RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
       LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
       ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
       PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
) 
