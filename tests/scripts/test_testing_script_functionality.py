import shutil
from unittest.mock import MagicMock, patch, Mock
from collections import namedtuple
import os
import subprocess as sp
from pathlib import Path
import pytest
from argparse import Namespace
import sys
import tempfile

from afni_test_utils import functions_for_ci_tests as ci_funcs
from afni_test_utils.container_execution import (
    run_containerized,
    VALID_MOUNT_MODES,
    unparse_args_for_container,
    check_user_container_args,
)

TESTS_DIR = Path(__file__).parent.parent


def test_check_user_container_args():

    # basic usage
    check_user_container_args(TESTS_DIR)

    # test-data-only is a valid value for source_mode
    check_user_container_args(
        TESTS_DIR,
        image_name="an_image",
        only_use_local=False,
        source_mode="test-data-only",
    )

    # Build dir outside of source should work
    dir_outside_src = tempfile.mkdtemp()
    check_user_container_args(
        TESTS_DIR,
        image_name="an_image",
        only_use_local=False,
        source_mode="host",
        build_dir=dir_outside_src,
    )
    # Value error should be raised if build is in source
    with pytest.raises(ValueError):
        check_user_container_args(
            TESTS_DIR,
            image_name="an_image",
            only_use_local=False,
            source_mode="host",
            build_dir=str(TESTS_DIR),
        )

    # reuse-build conflicts with build-dir because reuse implies container build dir
    with pytest.raises(ValueError):
        check_user_container_args(
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
        check_user_container_args(
            TESTS_DIR,
            image_name="an_image",
            only_use_local=False,
            source_mode="test-code",
            build_dir=dir_outside_src,
        )
    with pytest.raises(ValueError):
        check_user_container_args(
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
            check_user_container_args(
                TESTS_DIR,
                image_name="afni/afni_cmake_build",
                only_use_local=False,
                source_mode="host",
            )
        with pytest.raises(ValueError):
            check_user_container_args(
                TESTS_DIR,
                image_name="afni/afni_cmake_build",
                only_use_local=False,
                build_dir=tempfile.mkdtemp(),
            )
    finally:
        os.getuid = getuid


def test_get_test_cmd_args():
    # FakeRepo = namedtuple("Repo", ["dirty"])
    # with patch.object(datalad.Dataset, 'repo',spec=FakeRepo(dirty=False)) as mock_method:

    cmd_args = ci_funcs.get_test_cmd_args()
    assert cmd_args == ["scripts"]

    cmd_args = ci_funcs.get_test_cmd_args(verbose=True)
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


def test_unparse_args_for_container():
    user_args = {}
    expected = """ local"""
    converted = unparse_args_for_container(**user_args)
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
    converted = unparse_args_for_container(**user_args)
    assert converted == expected

    user_args = {
        "debug": False,
        "extra_args": "-k hello --trace",
        "use_all_cores": False,
        "coverage": True,
        "verbose": False,
    }
    expected = """ --extra-args="-k hello --trace" --coverage local"""
    converted = unparse_args_for_container(**user_args)
    assert converted == expected

    # underscores should be converted for any kwargs passed through (when
    # their value is True at least)
    user_args = {"arbitrary_kwarg_with_underscores": True}

    converted = unparse_args_for_container(**user_args)
    assert "--arbitrary-kwarg-with-underscores local" in converted

    # --reuse-build should
    user_args = {"reuse_build": True}

    converted = unparse_args_for_container(**user_args)
    assert "--build-dir=/opt/afni/build" in converted


def test_generate_cmake_command_as_required():
    adict = {"build_dir": tempfile.mkdtemp()}
    output = ci_funcs.generate_cmake_command_as_required(TESTS_DIR, adict)
    assert "cmake -GNinja" in output
