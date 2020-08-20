from argparse import Namespace
from collections import namedtuple
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import os
import pytest
import runpy
import shlex
import shutil
import subprocess
import subprocess as sp
import sys
import tempfile


from afni_test_utils import run_tests_func
from afni_test_utils import run_tests_examples
from afni_test_utils import functions_for_ci_tests as ci_funcs
from afni_test_utils import container_execution as ce


TESTS_DIR = Path(__file__).parent.parent
SCRIPT = Path(shutil.which("run_afni_tests.py"))




@patch("afni_test_utils.run_tests_func.subprocess")
def test_run_tests(mocked_sp):
    run_mock = MagicMock()
    run_mock.returncode = 0
    mocked_sp.run.return_value = run_mock
    args_in = {}
    with pytest.raises(SystemExit) as err:
        run_tests_func.run_tests(TESTS_DIR, **args_in)
    assert err.typename == "SystemExit"
    assert err.value.code == 0
    default_cmd = 'pytest scripts -r=Exs --show-capture=no --tb=no --verbose -s'
    mocked_sp.run.assert_called_with(default_cmd, shell=True)

    tmpdir = tempfile.mkdtemp()
    args_in = {"coverage": True, "build_dir": tmpdir}
    with pytest.raises(SystemExit) as err:
        run_tests_func.run_tests(TESTS_DIR, **args_in)
    assert err.typename == "SystemExit"
    assert err.value.code == 0

    expected_call = (
        f"cd {tmpdir};cmake -GNinja {TESTS_DIR.parent};ARGS='scripts "
        "-r=Exs --show-capture=no --tb=no --verbose -s "
        "--cov=targets_built --cov-report xml:$PWD/coverage.xml' ninja "
        "pytest"
        )




    run_calls = mocked_sp.run.assert_called_with(expected_call, shell=True,)


def test_run_tests_help_works():
    res = runpy.run_path(str(SCRIPT))

    for help_arg in "-h --help -help examples".split():
        res["sys"].argv = [SCRIPT.name, help_arg]
        with pytest.raises(SystemExit) as err:
            # Run main function while redirecting to /dev/null
            stdout_ = sys.stdout  # Keep track of the previous value.
            sys.stdout = open(os.devnull, "w")
            res["main"]()
            sys.stdout = stdout_  # restore the previous stdout.
        assert err.typename == "SystemExit"
        assert err.value.code == 0
        for dep in "datalad pytest afnipy run_tests".split():
            assert dep not in res


@patch("afni_test_utils.minimal_funcs_for_run_tests_cli.dir_path")
def test_examples_parse_correctly(mocked_dirpath):

    # dir_path needs to be mocked to prevent errors being raise for
    # non-existent paths
    mocked_dirpath.side_effect = lambda x: str(Path(x).expanduser())
    stdout_ = sys.stdout  # Keep track of the previous value.

    for name, example in run_tests_examples.examples.items():
        # Generate the 'sys.argv' for the example
        arg_list = shlex.split(example.splitlines()[-1])[1:]

        # Execute the script so that it can be run.
        res = runpy.run_path(str(SCRIPT))

        res["sys"].argv = [SCRIPT.name, *arg_list]
        res["main"].__globals__["run_tests"] = MagicMock(side_effect=SystemExit(0))
        res["main"].__globals__["run_containerized"] = MagicMock(side_effect=SystemExit(0))
        with pytest.raises(SystemExit) as err:
            # Run main function while redirecting to /dev/null
            sys.stdout = open(os.devnull, "w")
            res["main"]()
            sys.stdout = stdout_  # restore the previous stdout.
        assert err.typename == "SystemExit"
        assert err.value.code == 0

        if "local" in arg_list:
            res["main"].__globals__["run_tests"].assert_called_once()
        elif "container" in arg_list:
            res["main"].__globals__["run_containerized"].assert_called_once()

    sys.stdout = stdout_  # restore the previous stdout.


def test_check_user_container_args():

    # basic usage
    ce.check_user_container_args(TESTS_DIR)

    # test-data-only is a valid value for source_mode
    ce.check_user_container_args(
        TESTS_DIR,
        image_name="an_image",
        only_use_local=False,
        source_mode="test-data-only",
    )

    # Build dir outside of source should work
    dir_outside_src = tempfile.mkdtemp()
    ce.check_user_container_args(
        TESTS_DIR,
        image_name="an_image",
        only_use_local=False,
        source_mode="host",
        build_dir=dir_outside_src,
    )
    # Value error should be raised if build is in source
    with pytest.raises(ValueError):
        ce.check_user_container_args(
            TESTS_DIR,
            image_name="an_image",
            only_use_local=False,
            source_mode="host",
            build_dir=str(TESTS_DIR),
        )

    # reuse-build conflicts with build-dir because reuse implies container build dir
    with pytest.raises(ValueError):
        ce.check_user_container_args(
            TESTS_DIR,
            image_name="an_image",
            only_use_local=False,
            source_mode="host",
            build_dir=dir_outside_src,
            reuse_build=True,
        )

    # test-code mounting conflicts with build-dir and reuse-build because test-code implies
    # using installed version of afni
    with pytest.raises(ValueError):
        ce.check_user_container_args(
            TESTS_DIR,
            image_name="an_image",
            only_use_local=False,
            source_mode="test-code",
            build_dir=dir_outside_src,
        )
    with pytest.raises(ValueError):
        ce.check_user_container_args(
            TESTS_DIR,
            image_name="an_image",
            only_use_local=False,
            source_mode="test-code",
            reuse_build=True,
        )


def test_check_user_container_args_with_root():
    # this contains a bit of a hack because I couldn't figure out how to patch
    # ci_funcs.os on a test specific basis
    from os import getuid, listdir

    os.getuid = MagicMock(return_value="0")
    try:
        with pytest.raises(ValueError):
            ce.check_user_container_args(
                TESTS_DIR,
                image_name="afni/afni_cmake_build",
                only_use_local=False,
                source_mode="host",
            )
        with pytest.raises(ValueError):
            ce.check_user_container_args(
                TESTS_DIR,
                image_name="afni/afni_cmake_build",
                only_use_local=False,
                build_dir=tempfile.mkdtemp(),
            )
    finally:
        os.getuid = getuid


def test_get_test_cmd_args():
    cmd_args = ci_funcs.get_test_cmd_args(overwrite_args="")
    assert not cmd_args

    # Check default commands
    cmd_args = ci_funcs.get_test_cmd_args()
    assert cmd_args == ['scripts', '--tb=no', '--no-summary', '--show-capture=no']

    cmd_args = ci_funcs.get_test_cmd_args(verbose=3)
    assert "--showlocals" in cmd_args



def test_configure_parallelism():
    _environ = dict(os.environ)  # or os.environ.copy()
    try:

        # check use_all_cores works
        if "OMP_NUM_THREADS" in os.environ:
            del os.environ["OMP_NUM_THREADS"]
        cmd_args = ci_funcs.configure_parallelism([], use_all_cores=True)
        assert "--workers" in cmd_args
        assert os.environ["OMP_NUM_THREADS"] == "1"

        if "OMP_NUM_THREADS" in os.environ:
            del os.environ["OMP_NUM_THREADS"]
        cmd_args = ci_funcs.configure_parallelism([], use_all_cores=False)
        assert os.environ.get("OMP_NUM_THREADS")

    finally:
        os.environ.clear()
        os.environ.update(_environ)


def test_configure_for_coverage():
    cmd_args = ["scripts"]
    # Coverage should fail without a build directory
    with pytest.raises(ValueError):
        out_args = ci_funcs.configure_for_coverage(cmd_args, coverage=True)
    _environ = dict(os.environ)  # or os.environ.copy()
    try:

        if "CFLAGS" in os.environ:
            del os.environ["CFLAGS"]
        if "LDFLAGS" in os.environ:
            del os.environ["LDFLAGS"]
        if "CXXFLAGS" in os.environ:
            del os.environ["CXXFLAGS"]

        # Check coverage flags are added
        out_args = ci_funcs.configure_for_coverage(
            cmd_args, coverage=True, build_dir="something"
        )
        cov_args = ["--cov=targets_built", "--cov-report", "xml:$PWD/coverage.xml"]
        assert all(x in out_args for x in cov_args)
        assert (
            os.environ.get("CXXFLAGS")
            == "-g -O0 -Wall -W -Wshadow -Wunused-variable -Wunused-parameter -Wunused-function -Wunused -Wno-system-headers -Wno-deprecated -Woverloaded-virtual -Wwrite-strings -fprofile-arcs -ftest-coverage"
        )
        assert (
            os.environ.get("CFLAGS") == "-g -O0 -Wall -W -fprofile-arcs -ftest-coverage"
        )
        assert os.environ.get("LDFLAGS") == "-fprofile-arcs -ftest-coverage"

        # Check vars are not inappropriately set
        if "CFLAGS" in os.environ:
            del os.environ["CFLAGS"]
        if "LDFLAGS" in os.environ:
            del os.environ["LDFLAGS"]
        if "CXXFLAGS" in os.environ:
            del os.environ["CXXFLAGS"]
        out_args = ci_funcs.configure_for_coverage(
            cmd_args, coverage=False, build_dir="something"
        )
        assert not any([os.environ.get(x) for x in "CFLAGS CXXFLAGS LDFLAGS".split()])

    finally:
        os.environ.clear()
        os.environ.update(_environ)





def test_generate_cmake_command_as_required():
    adict = {"build_dir": tempfile.mkdtemp()}
    output = ci_funcs.generate_cmake_command_as_required(TESTS_DIR, adict)
    assert "cmake -GNinja" in output




def test_unparse_args_for_container():
    user_args = {}
    expected = """ local"""
    converted = ce.unparse_args_for_container(**user_args)
    assert converted == expected

    user_args = {
        "build_dir": "/saved/afni/build",
        "debug": True,
        "extra_args": None,
        "ignore_dirty_data": False,
        "image_name": "afni/afni_cmake_build",
        "source_mode": "host",
        "only_use_local": True,
        "use_all_cores": False,
        "coverage": True,
        "verbose": False,
    }
    expected = """ --build-dir=/opt/afni/build --debug --coverage local"""
    converted = ce.unparse_args_for_container(**user_args)
    assert converted == expected

    user_args = {
        "debug": False,
        "extra_args": "-k hello --trace",
        "use_all_cores": False,
        "coverage": True,
        "verbose": False,
    }
    expected = """ --extra-args="-k hello --trace" --coverage local"""
    converted = ce.unparse_args_for_container(**user_args)
    assert converted == expected

    # underscores should be converted for any kwargs passed through (when
    # their value is True at least)
    user_args = {"arbitrary_kwarg_with_underscores": True}

    converted = ce.unparse_args_for_container(**user_args)
    assert "--arbitrary-kwarg-with-underscores local" in converted

    # --reuse-build should
    user_args = {"reuse_build": True}

    converted = ce.unparse_args_for_container(**user_args)
    assert "--build-dir=/opt/afni/build" in converted


@patch("afni_test_utils.container_execution.docker")
def test_run_containerized(mocked_docker):
    container = Mock()
    container.logs.return_value = [b"success"]
    client = Mock()
    client.images.search.return_value = True
    client.containers.run.return_value = container
    mocked_docker.from_env.return_value = client

    # Calling with coverage=True should result in --coverage being in the
    # docker run call
    ce.run_containerized(
        TESTS_DIR,
        **{
            "image_name": "afni/afni_cmake_build",
            "only_use_local": True,
            "coverage": True,
        },
    )
    run_calls = client.containers.run.call_args_list
    assert "--coverage" in run_calls[0][0][1]


@patch("afni_test_utils.container_execution.docker")
def test_run_containerized_fails_with_unknown_image(mocked_docker):
    container = Mock()
    container.logs.return_value = [b"success"]
    client = Mock()
    client.images.search.side_effect = ValueError()
    mocked_docker.from_env.return_value = client

    # The image needs to exist locally with only_use_local
    with pytest.raises(ValueError):
        ce.run_containerized(
            TESTS_DIR, **{"image_name": "unknown_image", "only_use_local": True,}
        )


def test_setup_docker_env_and_vol_settings():
    # basic usage
    ce.setup_docker_env_and_vol_settings(TESTS_DIR,)

    # Confirm source directory is mounted
    source_dir, *_ = ce.get_path_strs_for_mounting(TESTS_DIR)
    docker_kwargs = ce.setup_docker_env_and_vol_settings(
        TESTS_DIR, **{"source_mode": "host"},
    )
    assert docker_kwargs.get("volumes").get(source_dir)
    expected = "/opt/afni/build,/opt/user_pip_packages"
    assert docker_kwargs.get("environment")["CHOWN_EXTRA"] == expected
    assert docker_kwargs["environment"].get("CONTAINER_UID")

    # Confirm test-data directory is mounted
    _, data_dir, *_ = ce.get_path_strs_for_mounting(TESTS_DIR)
    docker_kwargs = ce.setup_docker_env_and_vol_settings(
        TESTS_DIR, **{"source_mode": "test-data-only"},
    )
    assert docker_kwargs.get("volumes").get(data_dir)
    expected = "/opt/afni/src/tests/afni_ci_test_data"
    assert docker_kwargs.get("environment")["CHOWN_EXTRA"] == expected
    assert not docker_kwargs["environment"].get("CONTAINER_UID")

    # Confirm tests directory is mounted and file permissions is set correctly
    _, data_dir, *_ = ce.get_path_strs_for_mounting(TESTS_DIR)
    docker_kwargs = ce.setup_docker_env_and_vol_settings(
        TESTS_DIR, **{"source_mode": "test-code"},
    )
    assert docker_kwargs.get("volumes").get(str(TESTS_DIR))
    expected = "/opt/afni/install,/opt/user_pip_packages"
    assert docker_kwargs.get("environment")["CHOWN_EXTRA"] == expected
    assert docker_kwargs["environment"].get("CONTAINER_UID")

    # Confirm build directory is mounted
    _, data_dir, *_ = ce.get_path_strs_for_mounting(TESTS_DIR)
    docker_kwargs = ce.setup_docker_env_and_vol_settings(
        TESTS_DIR, **{"build_dir": data_dir},
    )
    assert docker_kwargs.get("volumes").get(data_dir)
    assert not docker_kwargs["environment"].get("CONTAINER_UID")
