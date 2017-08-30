project(coxplot)
cmake_minimum_required(VERSION 3.2)
include(FindMotif)

set(COXPLOT_INSTALL_BIN_DIR "${CMAKE_INSTALL_PREFIX}/bin/${project}")
set(COXPLOT_INSTALL_LIB_DIR "${CMAKE_INSTALL_PREFIX}/lib/${project}")
set(COXPLOT_INSTALL_STA_DIR "${CMAKE_INSTALL_PREFIX}/static/${project}")
set(COXPLOT_INSTALL_INCLUDE_DIR "${CMAKE_INSTALL_PREFIX}/include/${project}")

# Until I have setup modern use of target properties I will export this.
set(COXPLOT_INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR} PARENT_SCOPE)



set(COXPLOT_SRCS  color.c curve.c find_color_name.c frame.c frstpt.c labmod.c
line.c memplt.c perim.c periml.c phdot.c phline.c plot_cox.c plot_motif.c
plot_ps.c plot_ps2.c plot_strip.c plot_ts.c plot_x11.c plotpak.inc point.c
points.c ppak_commons.c ppak_perim.c ppak_pwrit.c ppak_pwritf.c ppak_srface.c
pwrit.c pwritf.c set.c setdsh.c setfrm.c setlin.c setw.c srface.c tick4.c
vector.c zzaxxx.c zzaxyy.c zzchar.c zzclip.c zzlabl.c zzlgin.c zzline.c
zzlinx.c zzliny.c zzlogx.c zzlogy.c zzperi.c zzphph.c zzphys.c 
)

add_library(coxplot ${COXPLOT_SRCS} ../machdep.h)
target_link_libraries(coxplot m converted_from_fortran ${MOTIF_LIBRARIES})
target_include_directories(coxplot PRIVATE ${MOTIF_INCLUDE_DIR})
target_include_directories(coxplot PUBLIC ${COXPLOT_INCLUDE_DIRS})

set_target_properties(coxplot PROPERTIES
	PUBLIC_HEADER "coxplot.h"
)

install(TARGETS coxplot
	EXPORT CoxplotTargets
	RUNTIME DESTINATION "${COXPLOT_INSTALL_BIN_DIR}" COMPONENT bin
	LIBRARY DESTINATION "${COXPLOT_INSTALL_LIB_DIR}" COMPONENT shlib
	ARCHIVE DESTINATION "${COXPLOT_INSTALL_STA_DIR}"
	PUBLIC_HEADER DESTINATION "${COXPLOT_INSTALL_INCLUDE_DIR}"
	COMPONENT dev
)
