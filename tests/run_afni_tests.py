#!/usr/bin/env python3
# For the most robust results this script is used for continuous integration
# testing and should be executed within the developer docker container (see
# .circleci/config.yml)
import os
import sys
import subprocess
import argparse
from pathlib import Path

from afni_test_utils.container_execution import VALID_MOUNT_MODES, run_containerized
from afni_test_utils.exceptionhook import setup_exceptionhook


if "container" not in sys.argv:
    # When using container dependencies should be minimal: docker, docker-py
    from afni_test_utils.run_tests_func import run_tests

    # This script should be able to import from afnipy, otherwise something is
    # wrong. Passing in an installation directory is an exception to this...
    # This could be enhance to confirm that the correct afnipy is used.
    if "--abin" not in ' '.join(sys.argv):
        try:
            import afnipy
        except ImportError:
            err_txt = "Tried and failed to import from afnipy. To solve this either install afnipy or define the installation directory using the --abin flag."
            sys.exit(ImportError(err_txt))


def parse_user_args():
    parser = argparse.ArgumentParser(
        description="Run AFNI's test suite.", add_help=False,
    )
    parser.add_argument(
        "--help", "-help", "-h", dest="help", action="store_true",
        help="show this help message and exit",
    )
    parser.add_argument(
        "--extra-args",
        help=(
            "This should be a quoted string that is passed directly "
            "through to pytest. e.g. --extra-args='-k gui --trace'. "
            "Passing --help through to pytest will give you a sense "
            "of all the possibilities... "
        ),
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Increase the verbosity of pytest."
    )

    dir_for_build_type = parser.add_mutually_exclusive_group()
    dir_for_build_type.add_argument(
        "--build-dir",
        metavar="DIR",
        type=dir_path,
        help=(
            "Use the 'pytest' target from the cmake build system at "
            "this location. Requires ninja. This is convenient because "
            "it enables within-build-tree-testing so you don't have to "
            "install and you don't accidentally test the wrong programs "
            "due to incorrect PATH etc "
        ),
    )
    dir_for_build_type.add_argument(
        "--abin",
        metavar="DIR",
        type=dir_path,
        help=(
            "Provide the path to the installation directory of AFNI "
            "produced by the make build system "
        ),
    )

    # Options that affect threading
    thread_management = parser.add_mutually_exclusive_group()
    thread_management.add_argument(
        "--debug",
        action="store_true",
        dest="debug",
        help="Do not catch exceptions and show exception traceback (Drop into pdb debugger).",
    )
    thread_management.add_argument(
        "--use-all-cores",
        action="store_true",
        dest="use_all_cores",
        help="Make use of all cpus for tests (requires pytest-parallel).",
    )

    parser.add_argument(
        "--ignore-dirty-data",
        action="store_true",
        dest="ignore_dirty_data",
        help="Do not fail if the CI test data repository has uncommitted modifications",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Use codecov for test coverage (needs --build-dir).",
    )

    subparsers = parser.add_subparsers(
        dest="subparser",
        title="subcommands",
        description="valid subcommands (one required)",
    )
    # CLI group for running tests in a container
    container = subparsers.add_parser(
        "container",
        help="Running tests in an AFNI development container requires a "
        "docker installation and the python docker package",
    )

    container.add_argument(
        "--source-mode",
        choices=VALID_MOUNT_MODES,
        help=(
            "This defines how much of the source code on the host is "
            "used when running tests in the container. 'host' mounts "
            "the whole repo from the local filesystem during the tests. "
            "'test-code' only includes the tests sub-directory but is "
            "useful as it allows a different version of the test tree "
            "to be used from code that is installed in the container. "
            "'test-data-only', should rarely be needed, but only mounts the "
            "tests/afni_ci_test_data sub-directory into the container. "
            "Mounting directories into the container has implications "
            "for file permissions. If this option is not used, no "
            "issues occurs as all files are owned by the user in the "
            "container. If 'host' is chosen, AFNI's source code is "
            "mounted into the container. The source directory is owned "
            "by the host user, so the container user is changed to this "
            "id and the build and home directory are appropriately "
            "chowned. If 'test-data-only' is used, privileged permissions "
            "will be required to transfer ownership of the test data "
            "back to the host user. "
        ),
    )
    container.add_argument(
        "--image-name",
        help="Image used for testing container. Default is likely something like afni/afni_cmake_build",
    )
    container.add_argument(
        "--only-use-local",
        action="store_true",
        help="Raise error if image name does not exist locally.",
    )
    container.add_argument(
        "--reuse-build",
        action="store_true",
        help="Use build dir in container (conflicts with --build-dir).",
    )

    container = subparsers.add_parser(
        "local",
        help=(
            "Running tests on the host requires additional "
            "dependencies. Consider something like the following "
            "command 'conda env create -f environment.yml;conda "
            "activate afni_dev' "
        ),
    )

    args = parser.parse_args()
    if args.help:
        sys.exit(parser.print_help())
    if not args.subparser:
        sys.exit(ValueError(
            f"You must specify a subcommand (one of {list(subparsers.choices.keys())})"
        ))
    return args


def dir_path(string):
    dir_in = Path(string).expanduser()
    if dir_in.exists():
        return str(dir_in)
    else:
        raise NotADirectoryError(string)


def test_dir_args_become_absolute():
    args_dict = {
        "abin": "scripts",
        "build_dir": "~/scripts",
    }

    expected = {
        "abin": str(Path("scripts").absolute()),
        "build_dir": str(Path("~/scripts").expanduser().absolute()),
    }
    make_dir_args_absolute(args_dict)
    assert args_dict == expected


def make_dir_args_absolute(args_dict):
    for k in ["abin", "build_dir"]:
        if k in args_dict:
            args_dict[k] = str(Path(args_dict[k]).expanduser().absolute())


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
    else:
        run_tests(tests_dir, **args_dict)


if __name__ == "__main__":

    main()
