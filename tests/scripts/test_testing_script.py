# This sys module is a little weird because it is testing a python file that
# is not on the path and is not in a child directory of the one this script
# resides
from unittest.mock import MagicMock, patch, Mock
import os
import shlex
from pathlib import Path
import pytest
import sys
from argparse import Namespace
import subprocess
import tempfile
import shutil
import runpy
from afni_test_utils import run_tests_func
from afni_test_utils import run_tests_examples

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
    mocked_sp.run.assert_called_with("pytest scripts", shell=True)

    tmpdir = tempfile.mkdtemp()
    args_in = {"coverage": True, "build_dir": tmpdir}
    with pytest.raises(SystemExit) as err:
        run_tests_func.run_tests(TESTS_DIR, **args_in)
    assert err.typename == "SystemExit"
    assert err.value.code == 0

    expected_call = f"cd {tmpdir};cmake -GNinja {TESTS_DIR.parent};ARGS='scripts --cov=targets_built --cov-report xml:$PWD/coverage.xml' ninja pytest"
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


@patch("afni_test_utils.run_tests_cli.dir_path")
def test_examples_parse_correctly(mocked_dirpath):

    # dir_path needs to be mocked to prevent errors being raise for
    # non-existent paths
    mocked_dirpath.side_effect = lambda x: str(Path(x).expanduser())

    for name, example in run_tests_examples.examples.items():
        # Generate the 'sys.argv' for the example
        arg_list = shlex.split(example.splitlines()[-1])[1:]

        # Execute the script so that it can be run.
        res = runpy.run_path(str(SCRIPT))

        res["sys"].argv = [SCRIPT.name, *arg_list]
        res["main"].__globals__["run_tests"] = MagicMock()
        res["main"].__globals__["run_containerized"] = MagicMock()
        # res['run_tests'] = MagicMock()
        res["main"]()
        if "local" in arg_list:
            res["main"].__globals__["run_tests"].assert_called_once()
        elif "container" in arg_list:
            res["main"].__globals__["run_containerized"].assert_called_once()
