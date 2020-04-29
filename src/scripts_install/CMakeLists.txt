# This file manages the installation of all scripts. In the future the R and python
# scripts might be migrated to packages

set(SCRIPT_PERMISSIONS "OWNER_READ;OWNER_WRITE;OWNER_EXECUTE;WORLD_EXECUTE;WORLD_READ")

# tcsh scripts (R related scripts are ignored if COMP_ADD_RSTATS is not set)
install(
  DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/
  DESTINATION ${AFNI_INSTALL_RUNTIME_DIR}
  COMPONENT tcsh
  FILES_MATCHING
  PATTERN "*" 
  PERMISSIONS ${SCRIPT_PERMISSIONS}
)

if(COMP_ADD_RSTATS)
# R scripts
install(
  DIRECTORY ../R_scripts/
  COMPONENT rstats
  DESTINATION ${AFNI_INSTALL_RUNTIME_DIR}
  FILES_MATCHING
  PATTERN "*R"
  PERMISSIONS ${SCRIPT_PERMISSIONS}
)

install(
  DIRECTORY ../scripts_for_r/
  COMPONENT rstats
  DESTINATION ${AFNI_INSTALL_RUNTIME_DIR}
  FILES_MATCHING
  PATTERN "*" 
  PERMISSIONS ${SCRIPT_PERMISSIONS}
)
endif()



file(
    GENERATE 
    OUTPUT ${CMAKE_BINARY_DIR}/make_sure_afnipy_installed.sh
    CONTENT "\
    \nif [ $# -lt 1 ]
    \n then
    \n     export py_interp=$(which python)
    \n else
    \n     export py_interp=$1
    \nfi
    \nif [ ! -f setup.py ]; 
    \nthen
    \n    echo This script should be run from the python_scripts directory
    \n    exit 1
    \nfi
    \nif [ ! $py_interp -c \"import afnipy\" ];
    \nthen
    \n    $py_interp setup.py develop
    \nfi
    "
    )
add_custom_command(
    OUTPUT ${CMAKE_BINARY_DIR}/.python_install_required 
    COMMAND echo Checking whether python is installed
    COMMAND if true;then echo hello;fi
    USES_TERMINAL
    )
# add_custom_target(
#   pytest
#   DEPENDS test_setup check_afnipy_installed
#   WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/afni_tests"
#   COMMAND ${CMAKE_COMMAND} --build ${CMAKE_CURRENT_BINARY_DIR}
#   COMMAND echo Running tests with modified path to use build binaries and scripts in the source tree...
#   COMMAND echo Prepending ${TESTING_PATHS}
#   COMMAND echo When using 'ninja pytest' one can define "ARGS" to pass additional arguments to pytest...
#   COMMAND ${CMAKE_COMMAND} -E env PATH=${PATH_FOR_TESTING}  ${Python_EXECUTABLE} -B -m pytest $$ARGS
#   USES_TERMINAL
# )

  #   add_custom_target(
  #     atlases_dir 
  #     ALL:
  #     VERBATIM
  #     COMMAND echo Data for distribution has been downloaded (ADD_ATLASES has been set to ON)
  #     DEPENDS ${CMAKE_BINARY_DIR}/afni_data 
  #     )

  # install(
  #   DIRECTORY ${CMAKE_BINARY_DIR}/afni_data/atlases/
  #   COMPONENT atlases
  #   DESTINATION ${AFNI_INSTALL_ATLAS_DIR}
  #   PATTERN '*'
  #   PERMISSIONS "WORLD_READ"
  # )

if(COMP_ADD_PYTHON) 
    if(STANDARD_PYTHON_INSTALL)
    # A standard installation of the python code is required to run the tests.
    # Using pip (or just setuptools) to install AFNI's python code has the
    # advantage that the code is installed into a specific python
    # interpretter/environment.  This is useful in many situations. To install
    # the python components of AFNI's installation using pip, execute the
    # following command from the src/python_scripts directory of the AFNI
    # codebase: 'pip install .', or 'python setup.py install'" The default
    # behavior of the cmake build is to install the package in development mode
    # during the build and to install into the python interpretters site
    # packages during and install.
    add_custom_target(install_afnipy COMMAND ${Python_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/../python_scripts/setup.py develop)

  else()
      # An alternative to installing using the current python interpretter is
      # to install the python files to abin. This has the advantage that they
      # are always available for use. The downside is that the installation
      # cannot be associated with a particular environment and so if the user
      # changes their python environment AFNI's python code may be available
      # but the pytho:n dependencies may not be.
      install(
        DIRECTORY ../python_scripts/scripts/
        COMPONENT python
        DESTINATION ${AFNI_INSTALL_RUNTIME_DIR}
        PATTERN "__pycache__" EXCLUDE
        PATTERN "*.pyc" EXCLUDE
        PATTERN "__init__.py" EXCLUDE
      )
    install(
          DIRECTORY ../python_scripts/afnipy
          COMPONENT python
          DESTINATION ${AFNI_INSTALL_RUNTIME_DIR}
          PATTERN "__pycache__" EXCLUDE
          PATTERN "*.pyc" EXCLUDE
        )
  endif()

  # Mimic make-builds distribution of all afni python files
  # RetroTS python files
  install(PROGRAMS
     ../pkundu/meica.py
     ../jzosky/RetroTS.py
     ../roopchansinghv/PsychoPy-NeuroFeedback-Demo/demoExpt.py
           DESTINATION ${AFNI_INSTALL_RUNTIME_DIR}
           PERMISSIONS ${SCRIPT_PERMISSIONS}
           COMPONENT python
   )
  install(
    DIRECTORY ../roopchansinghv/PsychoPy-NeuroFeedback-Demo/afniRTI
    DESTINATION ${AFNI_INSTALL_RUNTIME_DIR}
    PATTERN "__pycache__" EXCLUDE
    PERMISSIONS ${SCRIPT_PERMISSIONS}
   )

  install(
    DIRECTORY ../jzosky/lib_RetroTS
    COMPONENT python
    DESTINATION ${AFNI_INSTALL_RUNTIME_DIR}
    PATTERN "__pycache__" EXCLUDE
    PERMISSIONS ${SCRIPT_PERMISSIONS}
    PATTERN "*.pyc" EXCLUDE
  )

endif()
