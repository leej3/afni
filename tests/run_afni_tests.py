#!/usr/bin/env python3
# For the most robust results this script is used for continuous integration
# testing and should be executed within the developer docker container (see
# .circleci/config.yml)
import os
import sys

from pathlib import Path
from afni_test_utils.container_execution import VALID_MOUNT_MODES, run_containerized
from afni_test_utils.exceptionhook import setup_exceptionhook
from afni_test_utils.run_tests_examples import EXAMPLES
from afni_test_utils.run_tests_cli import parse_user_args, make_dir_args_absolute, needs_reduced_dependencies

# When using container dependencies should be minimal: docker, docker-py, python3.
# This section does a conditional import for when local dependencies should be
# installed. For situations in which help is requested or the dependencies
# should be containerized this section is skipped.
reduced_deps = needs_reduced_dependencies()

if not reduced_deps and 'local' in sys.argv:
    from afni_test_utils.run_tests_func import run_tests

    # This script should be able to import from afnipy, otherwise something is
    # wrong. Passing in an installation directory is an exception to this...
    # This could be enhanced to confirm that the correct afnipy is used.
    valid_without_afnipy = ["--abin","container"]
    if not any(pat in ' '.join(sys.argv) for pat in valid_without_afnipy):
        try:
            import afnipy
        except ImportError:
            err_txt = (
                "Tried and failed to import from afnipy. To solve this "
                "either install afnipy: \npip install "
                "afni/src/python_scripts\n or define the installation "
                "directory using the --abin flag. "
                )


            sys.exit(ImportError(err_txt))


def main(user_args=None):

    # parse user args:
    if not user_args:
        user_args = parse_user_args()

    args_dict = {k: v for k, v in vars(user_args).items() if v is not None}

    make_dir_args_absolute(args_dict)

    # Everything should be run from within the tests directory of the afni
    # source repository
    tests_dir = Path(__file__).resolve().parent
    os.chdir(tests_dir)

    if args_dict.get("debug"):
        setup_exceptionhook()

    if args_dict["subparser"] == "container":
        run_containerized(tests_dir, **args_dict)
    elif args_dict['subparser'] == 'examples':
        print(EXAMPLES)
        sys.exit(0)
    else:
        run_tests(tests_dir, **args_dict)


if __name__ == "__main__":

    main()
