import subprocess
import argparse
import sys
from afni_test_utils.container_execution import VALID_MOUNT_MODES
from pathlib import Path


def parse_user_args():
    parser = argparse.ArgumentParser(
        description=""" run_afni_tests.py is a wrapper script to help run
        tests for the AFNI suite of tools. This wrapping is an attempt to
        reduce the burden of executing tests and to facilitate the various
        usage patterns. Such usage patterns include: running the tests using
        dependencies installed on the local host; using a container to
        encapsulate most build/testing dependencies; making use of the cmake
        build system to make the iterative process of changing code and
        running tests easier; running the tests while making use of all the
        cores on the computer; subsetting the tests that are executed during a
        test run""",
        add_help=False,
    )
    parser.add_argument(
        "--help",
        "-help",
        "-h",
        dest="help",
        action="store_true",
        help="show this help message and exit",
    )
    parser.add_argument(
        "--extra-args",
        metavar="PYTEST_ARGS",
        help=(
            "This should be a quoted string that is passed directly "
            "through to pytest. e.g. --extra-args='-k gui --trace'. "
            "Passing --help through to pytest will give you a sense "
            "of all the possibilities... "
        ),
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Increase the verbosity of pytest"
    )
    parser.add_argument(
        "--filter-expr",
        "-k",
        metavar="EXPR",
        help=(
            "Expression for pytest to use to filter tests. Equivalent to passing "
            "--extra-args='-k EXPR'. "
        ),
    )
    parser.add_argument(
        "--file",
        "-f",
        help=("Relative path to test module to run. e.g. scripts/test_3dcopy.py"),
        type=dir_path,
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
    container = subparsers.add_parser("examples", help=("Show usage examples"),)

    args = parser.parse_args()
    if args.help:
        parser.print_help()
        sys.exit(0)
    if not args.subparser:
        sys.exit(
            ValueError(
                f"You must specify a subcommand (one of {list(subparsers.choices.keys())})"
            )
        )
    return args


def dir_path(string):
    dir_in = Path(string).expanduser()
    if dir_in.exists():
        return str(dir_in)
    else:
        raise NotADirectoryError(string)


def make_dir_args_absolute(args_dict):
    for k in ["abin", "build_dir"]:
        if k in args_dict:
            args_dict[k] = str(Path(args_dict[k]).expanduser().absolute())


def needs_reduced_dependencies():
    if any(x in sys.argv for x in ["-h", "-help", "--help"]):
        return True

    subparser_patterns = ["examples", "container"]
    if any(x in sys.argv for x in subparser_patterns):
        # Not sure if this is the sub parser so need to parse the
        # arguments to check
        parsed = parse_user_args()
        if parsed.subparser in subparser_patterns:
            return True

    return False
