#!/usr/bin/env python3
# This script is convoluted in an attempt to:
# a) provide help/examples without dependencies
# b) correctly execute tests in a container with minimal dependencies outside
#    the container
# c) provide informative errors outside of these circumstances for beginners
#    to the python world
# If it fails in the above, refactoring the code to a more traditional pattern
# would be desirable.
import os
import sys
from pathlib import Path
import importlib

try:
    minfunc = importlib.import_module(
        'afni_test_utils.minimal_funcs_for_run_tests_cli',
     )
except Exception as err:
    print(err)
    raise ImportError(
        f"If you are having issues importing you may want to "
        "confirm you have installed the required dependencies and, if "
        "you are using a tool that manages environments, that you have "
        "the appropriate environment. For installation consider installing miniconda and running "
        "the following from the tests directory in the afni repository:\n"
        "conda env create -f environment.yml   \n\n Additionally, if not using "
        "the cmake build, you should use the --abin option"
    )
from afni_test_utils.exceptionhook import setup_exceptionhook
from afni_test_utils.run_tests_examples import EXAMPLES, examples

# Examples and help should only need python3
# When using container dependencies should be minimal: docker, docker-py, python3.
# This section does a conditional import for when local dependencies should be
# installed. For situations in which help is requested or the dependencies
# should be containerized this section is skipped.
dep_reqs = minfunc.get_dependency_requirements()


if dep_reqs != 'minimal':
    if dep_reqs == 'container_execution':
        from afni_test_utils.container_execution import run_containerized
    else:
        from afni_test_utils.run_tests_func import run_tests
        # This script should be able to import from afnipy, otherwise something is
        # wrong. Passing in an installation directory is an exception to this...
        # This could be enhanced to confirm that the correct afnipy is used.
        afnipy_err = (
            "Tried and failed to import from afnipy. To solve this you "
            "can:\na install afnipy: \n\tpip install "
            "afni/src/python_scripts\nb) define AFNI's installation "
            "directory using the --abin flag"
            # c) set the env variable PYTHONPATH to the binary directory. "
            )

        if "--abin" not in sys.argv:
            if os.environ.get('PYTHONPATH'):
                raise ValueError(
                    "Using PYTHONPATH is not supported. Unset this --abin or install "
                    "afnipy into your current python interpretter. "
                    )
            try:
                import afnipy
            except ImportError:
                sys.exit(ImportError(afnipy_err))


def main(user_args=None):

    # parse user args:
    if not user_args:
        user_args = minfunc.parse_user_args()

    args_dict = {k: v for k, v in vars(user_args).items() if v is not None}

    minfunc.make_dir_args_absolute(args_dict)

    # Everything should be run from within the tests directory of the afni
    # source repository
    tests_dir = Path(__file__).resolve().parent
    os.chdir(tests_dir)

    if args_dict.get("debug"):
        setup_exceptionhook()

    if args_dict["subparser"] == "container":
        run_containerized(tests_dir, **args_dict)
    elif args_dict["subparser"] == "examples":
        if args_dict.get("explain"):
            print(EXAMPLES)
        else:
            print("\n".join(f"{k}:\n    {v}" for k, v in examples.items()))
        sys.exit(0)
    else:
        run_tests(tests_dir, **args_dict)


if __name__ == "__main__":

    main()
