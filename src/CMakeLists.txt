project(AFNI
        VERSION ${GIT_REPO_VERSION}
        DESCRIPTION "A package for the analysis of functional neuroimaging.")
set( AFNI_LIBRARY_PROPERTIES 
  BUILD_SHARED_LIBS TRUE
  POSITION_INDEPENDENT_CODE TRUE
)



include(CPack)
include(CMakePackageConfigHelpers)
include(FindX11)
include(FindMotif)
find_package(Xt REQUIRED)
FIND_LIBRARY(NETCDF_LIBRARY netcdf)

# This doesn't work. would be nice if it did:
include(CMakePrintHelpers)
set(greeting hello)
cmake_print_variables(greeting)
cmake_print_variables(NIFTI_INCLUDE_DIRS)
cmake_print_variables(CMAKE_C_COMPILER CMAKE_MAJOR_VERSION DOES_NOT_EXIST)


# Check cmake version
if(${CMAKE_VERSION} VERSION_LESS 3.12)
    cmake_policy(VERSION ${CMAKE_MAJOR_VERSION}.${CMAKE_MINOR_VERSION})
endif()

# Write out package version information
write_basic_package_version_file(
    MyLibConfigVersion.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY AnyNewerVersion
    )

# Packaging support
set(CPACK_PACKAGE_VENDOR "SSCC NIMH")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Analysis of Functional NeuroImaging")
set(CPACK_PACKAGE_VERSION_MAJOR ${PROJECT_VERSION_MAJOR})
set(CPACK_PACKAGE_VERSION_MINOR ${PROJECT_VERSION_MINOR})
set(CPACK_PACKAGE_VERSION_PATCH ${PROJECT_VERSION_PATCH})
  # To do: add licence here or point to correct path
# set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENCE")
# set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/README.md")
set(CPACK_SOURCE_GENERATOR "TGZ;ZIP")
set(CPACK_SOURCE_IGNORE_FILES
    /.git
    /dist
    /.*build.*
    /\\\\.DS_Store
)



# Find or fetch nifti_clib

# a prefix can be used to avoid collisions with pre-existsing installations of
# the nifti libraries
set(NIFTI_PACKAGE_PREFIX "AFNI_" CACHE STRING "Set the nifti package prefix")
# The prefix can be prepended to the exported targets in the cases where
# projects use target names with the prefixes in them for example
# AFNI_NIFTI::AFNI_nifti2 instead of NIFTI::nifti2
set(INCLUDE_PREFIX_IN_EXPORT OFF)
set(NIFTI_LIBRARY_PROPERTIES ${AFNI_LIBRARY_PROPERTIES} CACHE STRING "Set the nifti library properties to match AFNI" FORCE)
find_package(${NIFTI_PACKAGE_PREFIX}NIFTI 3 QUIET)
if (NOT "${${NIFTI_PACKAGE_PREFIX}NIFTI_FOUND}")
  include(FetchContent)
  FetchContent_Declare( nifti_repo
          GIT_REPOSITORY https://github.com/NIFTI-Imaging/nifti_clib
          GIT_TAG        v3.0.0 # or git <HASH> or git <branch>
          )
  FetchContent_GetProperties(nifti_repo)
  if(NOT nifti_repo_POPULATED)
      set(FETCHCONTENT_QUIET OFF)
      message(STATUS "Downloading nifti_clib from github ... please wait")
      FetchContent_Populate( nifti_repo )
      message(STATUS "download complete.")
      add_subdirectory(${nifti_repo_SOURCE_DIR} ${nifti_repo_BINARY_DIR})
  endif()
endif()


# add_library(AFNI::AFNI ALIAS AFNI) # this is required somewhere

set(AFNI_MAJOR_VERSION 17)
set(AFNI_MINOR_VERSION 1)
set(AFNI_PATCH_VERSION 12)
set(AFNI_VERSION ${AFNI_MAJOR_VERSION}.${AFNI_MINOR_VERSION}.${AFNI_PATCH_VERSION})

string(TIMESTAMP BUILD_DATE "%m %d %Y")
configure_file(AFNI_version.h.in "${CMAKE_CURRENT_BINARY_DIR}/AFNI_version.h" @ONLY)


# if this is disabled there are various files in the base directory that are
# required for some of the bundles. I think building libraries with these
# might be one way of solving this. another way might be to explicitly include
# the base directory from the child directories with something like
# "get_filename_component(PARENT_DIR ${MYPROJECT_DIR} DIRECTORY)"
include_directories(
	${CMAKE_CURRENT_SOURCE_DIR}
	${CMAKE_CURRENT_BINARY_DIR}
)


# TODO add specific flag for specific file
set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -DAFNI_DEBUG -DIMSEQ_DEBUG -DDISPLAY_DEBUG -DTHD_DEBUG")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DREAD_WRITE_64 -DLINUX2")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DUSE_TRACING") # XXX not in default cflags


# XXX remove dlcompat
# XXX remove jpeg-6b
add_subdirectory(scripts_install)
add_subdirectory(python_scripts)
add_subdirectory(R_scripts)



# bundled library (XXX to remove/package elsewhere)
macro(optional_bundle name)
	string(TOUPPER ${name} upper)

	option(USE_SYSTEM_${upper} "use system ${name} instead of bundled")
	if(USE_SYSTEM_${upper})
		find_package(${name} REQUIRED)
	else(USE_SYSTEM_${upper})
		add_subdirectory(${name})
	endif(USE_SYSTEM_${upper})
endmacro(optional_bundle)



add_subdirectory(niml)

foreach(bundled avovk coxplot crorden eispack gifti Audio
       ptaylor qhull svm volpack XmHTML converted_from_fortran rickr 3DEdge SUMA)
	optional_bundle(${bundled})
endforeach(bundled)

option(USE_GIFTI "use gifti")
if(USE_GIFTI)
	set_source_files_properties(gifti_choice.c PROPERTIES COMPILE_DEFINITIONS "HAVE_GIFTI")
endif(USE_GIFTI)

option(CHECK_FRAME_BUFFER "do not check the framebuffer before rendering (might be buggy)" YES)
if(NOT CHECK_FRAME_BUFFER)
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DGL_NO_CHECK_FRAME_BUFFER")
endif(NOT CHECK_FRAME_BUFFER)

file(GLOB AFOBJS "afni*.c")
list(APPEND AFOBJS pbar.c $<TARGET_OBJECTS:parser> mcw_graf.c)

file(GLOB T3OBJS  "to3d*.c")

file(GLOB MRI_OBJS "mri_*.c")
list(APPEND MRI_OBJS csfft.c mcw_glob.c mcw_malloc.c cox_render.c debugtrace.c ge4_header.c rcmat.c dmat44.c)
foreach(filename mri_affine.c mri_pc_pursuit.c mri_process_siemens.c mri_quantize.c mri_alphasim.c mri_wf.c mri_gwarp.c mri_pvmap.c)
   list(REMOVE_ITEM MRI_OBJS ${CMAKE_CURRENT_SOURCE_DIR}/${filename})
endforeach(filename)

file(GLOB THD_OBJS "thd_*.c")
list(APPEND THD_OBJS afni_vedit.c ktaub.c bilinear_warp3D.c)
foreach(filename thd_bstrap_corr.c thd_gifti.c thd_md5.c thd_rot3d_2byte.c
    thd_serialate.c thd_ttatlas_CA_EZ.c thd_Xdataset.c thd_base64.c
     thd_shearwarp.c)
  list(REMOVE_ITEM THD_OBJS "${CMAKE_CURRENT_SOURCE_DIR}/${filename}")
endforeach(filename)
file(GLOB EDT_OBJS "edt_*.c")

file(GLOB CS_OBJS "cs_*.c")
list(APPEND CS_OBJS multivector.c afni_environ.c cl2.c machdep.c afni_logger.c cl1.c powell_int.c powell_newuoa.c rhdd.c zfun.c svdlib.c)
list(REMOVE_ITEM CS_OBJS "${CMAKE_CURRENT_SOURCE_DIR}/cs_color.c")
list(REMOVE_ITEM CS_OBJS "${CMAKE_CURRENT_SOURCE_DIR}/cs_simult.c")
list(REMOVE_ITEM CS_OBJS "${CMAKE_CURRENT_SOURCE_DIR}/cs_symeig23.c")

file(GLOB SUMA_OBJS "suma_*.c")
list(REMOVE_ITEM SUMA_OBJS "${CMAKE_CURRENT_SOURCE_DIR}/suma_gifti.c")

list(APPEND MISC_OBJS afni_suma.c vol2surf.c list_struct.c nifti_statlib.c matrix.c gifti_choice.c misc_math.c)

list(APPEND SOMEAFOBJS $<TARGET_OBJECTS:parser> afni_warp.c pbar_color_defs.c afni_ports.c)
foreach(type byte complex float rgbyte short)
	list(APPEND SOMEAFOBJS "${CMAKE_CURRENT_BINARY_DIR}/afni_slice_${type}.c")
endforeach(type)

add_library(libheaders OBJECT 3ddata.h AFNI_label.h Amalloc.h afni_environ.h afni_suma.h
	afni_warp.h coxplot.h cs.h cs_qsort_small.h cs_sort_template.h
	debugtrace.h editvol.h eispack.h killer.h list_struct.h machdep.h
	mcw_glob.h mcw_malloc.h mri_dicom_stuff.h mri_warpfield.h mrilib.h
	multivector.h  tagset.h thd_atlas.h thd_compress.h thd_iochan.h
	thd_maker.h thd_ttatlas_CA_EZ.h thd_ttatlas_query.h vecmat.h vol2surf.h
  AFNI_version.h niml.h
)
target_include_directories(libheaders 
  PUBLIC 
  $<TARGET_PROPERTY:rickr,INTERFACE_INCLUDE_DIRECTORIES>
  $<TARGET_PROPERTY:converted_from_fortran,INTERFACE_INCLUDE_DIRECTORIES>
  $<TARGET_PROPERTY:coxplot,INTERFACE_INCLUDE_DIRECTORIES>
  $<TARGET_PROPERTY:nifti2,INTERFACE_INCLUDE_DIRECTORIES>
  )

file(GLOB AFNI_HIST_FILES "afni_history*.c")
foreach(filename afni_fimmer_compute.c afni_history.c afni_open.c
		afni_pcor_update.c afni_slice.c afni_vcheck.c ${AFNI_HIST_FILES})
	list(REMOVE_ITEM AFOBJS "${CMAKE_CURRENT_SOURCE_DIR}/${filename}")
endforeach(filename)

foreach(type byte float short)
	set(output_file "${CMAKE_CURRENT_BINARY_DIR}/afni_pcor_${type}.c")
	configure_file(afni_pcor_update.c "${output_file}" COPYONLY)
	set_source_files_properties("${output_file}" PROPERTIES COMPILE_DEFINITIONS "DTYPE=${type}")
	list(APPEND AFOBJS "${output_file}")
endforeach(type)

foreach(type byte complex float int rgba rgbyte short)
	set(output_file "${CMAKE_CURRENT_BINARY_DIR}/afni_slice_${type}.c")
	configure_file(afni_slice.c "${output_file}" COPYONLY)
	set_source_files_properties("${output_file}" PROPERTIES COMPILE_DEFINITIONS "DTYPE=${type}")
	list(APPEND AFOBJS "${output_file}")
endforeach(type)


function(configure_pcor lib_name definitions)
	set(output_file "${CMAKE_CURRENT_BINARY_DIR}/${lib_name}.c")
	configure_file(pcor.c "${output_file}" COPYONLY)
	set_source_files_properties("${output_file}" PROPERTIES COMPILE_DEFINITIONS "${definitions}")
	add_library(${lib_name} OBJECT "${output_file}")
endfunction(configure_pcor)
configure_pcor(pcor "REF_FLOAT_SINGLE")
configure_pcor(pcorsh "REF_FLOAT_SINGLE;VOX_SHORT")

# foreach(filename colfit colcalc parser)
# 	add_custom_command(OUTPUT "${filename}.c"
# 		COMMAND ${F2C_BIN} "${CMAKE_CURRENT_SOURCE_DIR}/${filename}.f"
# 		MAIN_DEPENDENCY "${filename}.f")
# endforeach(filename)


foreach(target model_beta model_constant model_conv_PRF model_conv_PRF_6
		model_conv_PRF_DOG model_conv_cosine4 model_conv_diffgamma
		model_convgamma model_convgamma2a model_demri_3 model_diffexp
		model_diffusion model_exp model_expMEMRI model_expMEMRI3
		model_expr2 model_gammavar model_linear model_linplusort
		model_michaelis_menton model_null model_quadratic
		model_sinewave_ap model_sinewave_apf model_squarewave_ap
		model_squarewave_apf model_trnglwave_ap model_trnglwave_apf
		model_zero plug_3Ddump_V2 plug_3ddot plug_3ddup plug_4Ddump
		plug_L1fit plug_afnihistory plug_aslA3D3 plug_betafit plug_clust
		plug_compress plug_coorder plug_copy plug_crender
		plug_deconvolve plug_delay_V2 plug_drawdset plug_edit
		plug_extract plug_fourier plug_hemisub plug_histog
		plug_histog_multi plug_imreg plug_lsqfit plug_maskave
		plug_maskcalc plug_nlfit plug_notes plug_nth_dataset plug_nudge
		plug_null plug_permtest plug_power plug_realtime plug_rename
		plug_render plug_reorder plug_roiedit plug_roiplot plug_scatplot
		plug_second_dataset plug_stats plug_stavg plug_tag
		plug_threshold plug_ttget plug_vol2surf plug_volreg
		plug_wavelets plug_zeropad
)
	add_library(${target} ${target}.c)
	target_link_libraries(${target} PUBLIC mri)
endforeach(target)

add_library(afobj OBJECT ${AFOBJS})
add_executable(afni $<TARGET_OBJECTS:afobj>)
foreach(target Xphace afni_open aiv)
  add_library(${target} ${target}.c)
  target_include_directories(${target} PUBLIC $<TARGET_PROPERTY:NIFTI::nifti2,INTERFACE_INCLUDE_DIRECTORIES> ${COXPLOT_INCLUDE_DIRS})
endforeach(target)

add_library(mri ${MRI_OBJS} ${THD_OBJS} ${EDT_OBJS} ${CS_OBJS} ${SUMA_OBJS} ${MISC_OBJS} ${SOMEAFOBJS} 
  ${AUDIO_OBJS} $<TARGET_OBJECTS:niml::niml> $<TARGET_OBJECTS:AFNI::rickr>)
add_library(mrix display.c imseq.c bbox.c xim.c xutil.c xutil_webber.c LiteClue.c)
add_library(parser OBJECT parser.c parser_int.c)
add_library(plug_drealtime plug_realtime.c)
add_library(plug_maxima plug_maxima.c maxima.c)
add_library(plug_retroicor plug_retroicor.c retroicor.c)

foreach(target 1dAstrip 1dBandpass 1dBport 1dCorrelate 1dFlagMotion 1dMarry
		1dTsort 1dUpsample 1dcat 1ddot 1dfft 1dgenARMA11 1dnorm 1dsum
		1dsvd 1dtranspose 24swap 2dImReg 2perm 2swap 3dABoverlap
		3dAFNIto3D 3dAFNItoANALYZE 3dAFNItoMINC 3dAFNItoNIFTI
		3dAFNItoNIML 3dAFNItoRaw 3dANALYZEtoAFNI 3dAcost 3dAnatNudge
		3dAnhist 3dAttribute 3dAutoTcorrelate 3dAutobox 3dAutomask
		3dBandpass 3dBlurInMask 3dBlurToFWHM 3dBrickStat 3dCM
		3dClipLevel 3dClustCount 3dClustSim 3dConformist 3dConvolve
		3dCountSpikes 3dDFT 3dDTeig 3dDTtoDWI 3dDWItoDT
		3dDegreeCentrality 3dDespike 3dEmpty 3dEntropy 3dErrtsCormat
		3dExtractGroupInCorr 3dExtrema 3dFDR 3dFFT 3dFWHM 3dFWHMx
		3dFourier 3dFriedman 3dGetrow 3dGroupInCorr 3dIntracranial
		3dInvFMRI 3dKruskalWallis 3dLFCD 3dLRflip 3dLSS 3dLocalACF
		3dLocalBistat 3dLocalHistog 3dLocalPV 3dLocalSVD 3dLocalstat
		3dMINCtoAFNI 3dMannWhitney 3dMean 3dMedianFilter 3dMultiThresh
       3dNormalityTest 3dNotes 3dNwarpAdjust 3dNwarpApply
		3dNwarpCalc 3dNwarpCat 3dNwarpFuncs 3dNwarpXYZ 3dOverlap
		3dPeriodogram 3dPolyfit 3dPval 3dQwarp 3dREMLfit 3dROIstats
		3dRank 3dRankizer 3dRegAna 3dRetinoPhase 3dRowFillin
		3dSetupGroupInCorr 3dSharpen 3dSpatNorm 3dStatClust 3dSynthesize
       3dTRfix 3dTagalign 3dTcat 3dTcorr1D 3dTcorrMap
		3dTcorrelate 3dTfilter 3dThreetoRGB 3dTnorm 3dToutcount
		3dToyProg 3dTproject 3dTqual 3dTshift 3dTsmooth 3dTsort
		3dTsplit4D 3dTwotoComplex 3dUndump 3dUnifize 3dUniformize
		3dUpsample 3dWarp 3dWarpDrive 3dWavelets 3dWilcoxon 3dWinsor
		3dXClustSim 3dXYZcat 3dZcat 3dZcutup 3dZeropad 3dZregrid
		3daxialize 3dbuc2fim 3dbucket 3dcopy 3ddelay 3ddot 3ddup 3dfim+
		3dfractionize 3dinfo 3dmaskSVD 3dmask_tool 3dmaskave 3dmatmult
		3dnewid 3dnoise 3dnvals 3dpc 3drefit 3drename 3drotate
		3dsvm_linpredict 3dtoXdataset 3dttest++ 3dvolreg 4swap AlphaSim
		DTIStudioFibertoSegments FIRdesign GLTsymtest Ifile RSFgen
		Vecwarp abut adwarp afni_vcheck apsearch bitvec byteorder
		cat_matvec cdf count dicom_hdr dicom_hinfo dicom_to_raw ent16
		epsim exx fdrval fftest float_scan from3d ftosh ge_header
		help_format ibinom im2niml images_equal imand imaver imcalc
		imcat imcutup imdump immask imrotate imstack imstat imupsam
		mayo_analyze mritopgm mycat myget nicat niccc nidset nimel
		niml_feedme nimltest nsize plugout_drive plugout_ijk plugout_tt
		plugout_tta quotize rmz rotcom rtfeedme sfim siemens_vision
		sqwave stimband strblast test_powell testcox tfim uncomment
		uniq_images unu warping_test whereami whirlgif
)
	add_executable(${target} ${target}.c)
	target_link_libraries(${target} PUBLIC mri mrix)
endforeach(target)

foreach(i "" 2 3)
	set(target 3dANOVA${i}) 
	add_executable(${target} ${target}.c 3dANOVA.lib)
	target_link_libraries(${target} PUBLIC mri mrix)
endforeach(i)

foreach(target 1dNLfit 1deval 1dmatcalc 3dDeconvolve 3dDetrend 3dTstat 3dcalc
		3dclust 3dhistog 3dmaskdump 3dmatcalc 3dmerge 3dproject 3dttest
		ccalc waver
)
	add_executable(${target} ${target}.c $<TARGET_OBJECTS:parser>)
	target_link_libraries(${target} PUBLIC mri mrix)
endforeach(target)
target_link_libraries(3dproject PUBLIC volpack)


add_executable(3dTfitter 3dTfitter.c thd_fitter.c thd_lasso.c)
add_executable(3dfim 3dfim.c afni_pcor_float.c ts.c)
add_executable(FD2 FD2.c ts.c mcw.c overfim.c $<TARGET_OBJECTS:pcorsh> csfft_AJ.c)
add_executable(fim2 fim2.c ts.c $<TARGET_OBJECTS:pcor>)
add_executable(imreg imreg.c $<TARGET_OBJECTS:pcor>)
add_executable(to3d ${T3OBJS})
add_executable(3danisosmooth 3danisosmooth.c DWIstructtensor.c)
add_executable(1dSEM 1dSEM.c sqrmat.c matrix.c)
add_executable(3dNLfim 3dNLfim.c)
add_executable(gwarp mri_gwarp.c)
add_executable(3dmaxima 3dmaxima.c maxima.c)
add_executable(3dDeconvolve_n 3dDeconvolve.c $<TARGET_OBJECTS:parser>)
add_executable(3dDeconvolve_f 3dDeconvolve.c $<TARGET_OBJECTS:parser>)
add_executable(3dAllineate 3dAllineate.c mri_genalign.c mri_genalign_util.c thd_correlate.c)
add_executable(3dECM 3dECM.c sparse_array.c)
add_executable(3dMSE 3dMSE.c sparse_array.c)
add_executable(1dgrayplot 1dgrayplot.c display.c)
add_executable(1dplot 1dplot.c display.c)
add_executable(3dretroicor 3dretroicor.c retroicor.c)
add_executable(3dedge3 3dedge3.c)


set_source_files_properties(3dDeconvolve_f PROPERTIES COMPILE_DEFINITIONS "FLOATIZE")
set_source_files_properties(gifti_choice.c PROPERTIES COMPILE_DEFINITIONS "DTYPE=${type}")

set_target_properties(afni PROPERTIES PUBLIC_HEADER "${AFNI_HEADERS}")



# target_include_directories(afni_warp PUBLIC ${COXPLOT_INCLUDE_DIRS})
target_include_directories(3dDeconvolve PUBLIC ${COXPLOT_INCLUDE_DIRS})
target_include_directories(3dDeconvolve_f PUBLIC ${COXPLOT_INCLUDE_DIRS})
target_include_directories(3dMSE PUBLIC ${COXPLOT_INCLUDE_DIRS})
target_include_directories(3dretroicor PUBLIC ${COXPLOT_INCLUDE_DIRS} ${CONVERTED_FROM_FORTRAN_INCLUDE_DIRS} $<TARGET_PROPERTY:NIFTI::nifti2,INTERFACE_INCLUDE_DIRECTORIES>)
target_include_directories(3DEdge PUBLIC ${CONVERTED_FROM_FORTRAN_INCLUDE_DIRS} ${COXPLOT_INCLUDE_DIRS})
target_include_directories(SUMA PUBLIC ${CONVERTED_FROM_FORTRAN_INCLUDE_DIRS} ${COXPLOT_INCLUDE_DIRS} ${3DEDGE_INCLUDE_DIRS})
target_include_directories(coxplot PUBLIC ${CONVERTED_FROM_FORTRAN_INCLUDE_DIRS} ${COXPLOT_INCLUDE_DIRS})
target_include_directories(eispack PUBLIC ${CONVERTED_FROM_FORTRAN_INCLUDE_DIRS})
target_include_directories(mri  PUBLIC  ${3DEDGE_INCLUDE_DIRS} ${AUDIO_INCLUDE_DIRS} ${COXPLOT_INCLUDE_DIRS} $<TARGET_PROPERTY:AFNI::rickr,INTERFACE_INCLUDE_DIRECTORIES> )
target_include_directories(mrix PUBLIC ${CMAKE_CURRENT_SOURCE_DIR} $<TARGET_PROPERTY:AFNI::XmHTML,INTERFACE_INCLUDE_DIRECTORIES> ${GIFTI_INCLUDE_DIRS} ${COXPLOT_INCLUDE_DIRS})
target_include_directories(afobj 
  PUBLIC ${CMAKE_CURRENT_SOURCE_DIR} 
  $<TARGET_PROPERTY:NIFTI::nifti2,INTERFACE_INCLUDE_DIRECTORIES>
  $<TARGET_PROPERTY:AFNI::XmHTML,INTERFACE_INCLUDE_DIRECTORIES> 
  ${GIFTI_INCLUDE_DIRS} ${COXPLOT_INCLUDE_DIRS})
target_include_directories(parser PUBLIC ${NIML_INCLUDE_DIRS} ${CONVERTED_FROM_FORTRAN_INCLUDE_DIRS} ${COXPLOT_INCLUDE_DIRS} )
target_include_directories(to3d PUBLIC ${MOTIF_INCLUDE_DIR} )
target_include_directories(1dplot PUBLIC  ${XT_INCLUDE_DIR} ${X11_INCLUDE_DIRS} )

foreach(target 3dfim 3dTfitter FD2 fim2 imreg gwarp 3danisosmooth 3dmaxima
       3dAllineate 3dECM 3dMSE 1dSEM 
		plug_drealtime plug_maxima plug_retroicor
)

   target_link_libraries(${target} PUBLIC mri mrix NIFTI::nifticdf)
endforeach(target)
target_link_libraries(3dretroicor PUBLIC mri converted_from_fortran mrix coxplot)
target_link_libraries(3dNLfim PUBLIC mri mrix ${CMAKE_DL_LIBS})

target_link_libraries(parser PUBLIC coxplot libheaders NIFTI::nifti2)
target_link_libraries(1dgrayplot PUBLIC mri coxplot ${XT_LIBRARIES})
target_link_libraries(1dplot PUBLIC mrix mri NIFTI::nifti2 ${X11_Xt_LIB} ${X11_LIBRARIES})
target_link_libraries(3dDeconvolve PUBLIC mri coxplot)
target_link_libraries(3dDeconvolve_f PUBLIC mri coxplot)
target_link_libraries(3dDeconvolve_n PUBLIC mri coxplot)
target_link_libraries(Xphace PUBLIC mrix NIFTI::nifti2)
target_link_libraries(afobj PUBLIC ${XT_LIBRARIES} mri mrix coxplot)
target_link_libraries(afni PUBLIC mri ${CMAKE_DL_LIBS})
target_link_libraries(afni_open PUBLIC mri)
target_link_libraries(aiv PUBLIC mrix NIFTI::nifti2)
# target_include_directories(aiv $<TARGET_PROPERTY:NIFTI::nifti2,INTERFACE_INCLUDE_DIRECTORIES>)

target_link_libraries(mri PUBLIC  libheaders mrix nifti2 nifticdf eispack netcdf m znz giftiio 3DEdge volpack
   ${XMHTML_LIBRARIES} converted_from_fortran ${XT_LIBRARIES})
target_link_libraries(mrix PUBLIC coxplot mri libheaders)
target_link_libraries(to3d PUBLIC mri mrix nifti2 ${MOTIF_LIBRARIES} ${XT_LIBRARIES})

target_link_libraries(3dedge3 PUBLIC mri)


# link remaining executables from rickr
add_executable(Dimon rickr/Dimon.c rickr/realtime.c)
add_executable(Dimon1 rickr/Dimon1.c rickr/realtime1.c)
add_executable(3dresample rickr/3dresample.c)

target_link_libraries(Dimon1 PUBLIC mri)
target_link_libraries(Dimon PUBLIC mri)
target_link_libraries(3dresample PUBLIC mri)


add_executable(3dTSgen 3dTSgen.c)
target_include_directories(3dTSgen PUBLIC ${COXPLOT_INCLUDE_DIRS} ${CONVERTED_FROM_FORTRAN_INCLUDE_DIRS})
target_link_libraries(3dTSgen mri NIFTI::nifti2 converted_from_fortran coxplot ${CMAKE_DL_LIBS})



# export(TARGETS afni SUMA NAMESPACE AFNI:: FILE AFNITargets.cmake)
# export(PACKAGE AFNI)
# find_package(AFNI should work because of the above)

# check the AFNITargets file and make sure you don't have the include directory included twice if you want clean cmake files : https://cliutils.gitlab.io/modern-cmake/chapters/install/installing.html
# install(TARGETS afni afobj
#         EXPORT AFNITargets
#         LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
#         ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
#         RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
#         INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
#         )




# Install makefile programs that are built by this project.
execute_process(
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
     COMMAND bash "-c" "make -s -f Makefile.INCLUDE prog_list")
file(READ ${CMAKE_CURRENT_SOURCE_DIR}/prog_list.txt ALL_PROGRAMS)
string(STRIP ${ALL_PROGRAMS} ALL_PROGRAMS)
string(REPLACE "\n" " "  ALL_PROGRAMS ${ALL_PROGRAMS})
separate_arguments(ALL_PROGRAMS)
set(PROGRAMS_BUILT "")
# message(all_progs:"${ALL_PROGRAMS}")
foreach(program ${ALL_PROGRAMS} mri mrix)
  if(TARGET ${program})
  list(APPEND PROGRAMS_BUILT ${program})
  endif()
endforeach()
message("progs_built:'${PROGRAMS_BUILT}'")
install(TARGETS ${PROGRAMS_BUILT}
       RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
       LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
       ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
       PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)  
# # First, make an install targets file (very similar to the one you made in the build directory):
# install(EXPORT AFNITargets
#         FILE AFNITargets.cmake
#         NAMESPACE AFNI::
#         DESTINATION lib/cmake/AFNI
#          )