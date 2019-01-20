add_subdirectory(common)
add_subdirectory(Motif)
add_library(XmHTML_objs OBJECT ${COMMON_SRCS} ${MOTIF_SRCS})
