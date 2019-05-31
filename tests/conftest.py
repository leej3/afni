import subprocess
import os
from pathlib import Path
from typing import Union
import pytest
import shutil
import inspect
import functools
import datetime
import datetime as dt
from scripts.utils import misc

pytest.register_assert_rewrite("scripts.utils.tools")
import scripts.utils.tools as tools
from scripts.utils.tools import get_current_test_name
import attr
import re

missing_dependencies = (
    "In order to download data an installation of datalad, wget, or "
    "curl is required. Datalad is recommended to restrict the amount of "
    "data downloaded. "
)

try:
    import datalad.api as datalad

except ImportError:
    raise NotImplementedError("Currently datalad is a dependency for testing.")

CURRENT_TIME = dt.datetime.strftime(dt.datetime.today(), "%Y_%m_%d_%H%M%S")

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def pytest_generate_tests(metafunc):
    if "python_interpreter" in metafunc.fixturenames:
        if metafunc.config.option.testpython2:
            metafunc.parametrize("python_interpreter", ["python3", "python2"])
        else:
            metafunc.parametrize("python_interpreter", ["python3"])


def get_output_dir():
    outdir = (
        Path(pytest.config.rootdir) / "output_of_tests" / ("output_" + CURRENT_TIME)
    )
    return outdir


def get_test_data_path():
    return Path(pytest.config.rootdir) / "afni_ci_test_data"


def get_test_comparison_dir(current_test_module: Union[str or Path]):
    # Aside from two user-defined conditions the comparison directory should exist
    comparison_data_needs_to_exist = not (
        pytest.config.getoption("--create_sample_output")
        or pytest.config.getoption("--save_sample_output")
    )

    # Get path to full comparison directory and download as required
    cmpr_path = get_base_comparison_dir_path()
    if not cmpr_path.exists() and comparison_data_needs_to_exist:
        raise ValueError(
            "You may wish to run tests with the --create_sample_output "
            "flag or generate output for future test sessions with "
            "--save_sample_output. "
        )

    # Construct the path for this specific test
    test_name = get_current_test_name()
    test_compare_dir = cmpr_path / current_test_module.name / test_name

    return test_compare_dir


def get_base_comparison_dir_path():
    comparison_dir = pytest.config.getoption("--diff_with_outdir") or (
        get_test_data_path() / "sample_test_output"
    )
    comparison_dir = Path(comparison_dir).absolute()
    return comparison_dir


def get_tests_data_dir():
    # Define hard-coded paths for now
    tests_data_dir = get_test_data_path()
    race_error_msg = (
        "A failed attempt and datalad download occurred. Running the "
        "tests sequentially once may help "
    )

    # datalad is required and the datalad repository is used for data.
    if not (tests_data_dir / ".datalad").exists():
        try:
            datalad.install(
                str(tests_data_dir), "https://github.com/afni/afni_ci_test_data.git"
            )
        except FileExistsError as e:
            # likely a race condition
            print(e)
            raise FileExistsError(race_error_msg)
        except FileNotFoundError:
            raise FileNotFoundError(race_error_msg)

    return tests_data_dir


@pytest.fixture(scope="function")
def data(request):
    """A function-scoped test fixture used for AFNI's testing. The fixture
    sets up output directories as required and provides the named tuple "data"
    to the calling function. The data object contains some fields convenient
    for writing tests like the output directory. Finally the data fixture
    handles test input data.files  listed in a data_paths dictionary (if
    defined within the test module) the fixture will download them to a local
    datalad repository as required. Paths should be listed relative to the
    repository base-directory.

    Args: request (pytest.fixture): A function level pytest request object
        providing information about the calling test function.

    Returns:
        collections.NameTuple: A data object for conveniently handling the specification
    """
    test_name = get_current_test_name()
    tests_data_dir = get_tests_data_dir()

    # Set module specific values:
    try:
        data_paths = request.module.data_paths
    except AttributeError:
        data_paths = {}

    module_outdir = get_output_dir() / Path(request.module.__file__).stem.replace(
        "test_", ""
    )
    test_logdir = module_outdir / get_current_test_name() / "captured_output"
    if not test_logdir.exists():
        os.makedirs(test_logdir, exist_ok=True)

    # This will be created as required later
    sampdir = tools.convert_to_sample_dir_path(test_logdir.parent)

    # start creating output dict, downloading test data as required
    out_dict = {
        k: misc.process_path_obj(v, tests_data_dir) for k, v in data_paths.items()
    }

    # Get the comparison directory and check if it needs to be downloaded
    comparison_dir = get_test_comparison_dir(module_outdir)

    # Define output for calling module and get data as required:
    out_dict.update(
        {
            "module_outdir": module_outdir,
            "outdir": module_outdir / get_current_test_name(),
            "sampdir": sampdir,
            "logdir": test_logdir,
            "comparison_dir": comparison_dir,
            "base_comparison_dir": get_base_comparison_dir_path(),
            "base_outdir": get_output_dir(),
            "test_name": test_name,
        }
    )

    DataClass = attr.make_class(
        test_name + "_data", [k for k in out_dict.keys()], slots=True
    )
    return DataClass(*[v for v in out_dict.values()])


# configure keywords that alter test collection
def pytest_addoption(parser):
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run slow tests whose execution time is on the order of many seconds)",
    )
    parser.addoption(
        "--runveryslow",
        action="store_true",
        default=False,
        help="run very slow tests whose execution time is on the order "
        "of many minutes to hours ",
    )
    parser.addoption(
        "--diff_with_outdir",
        default=None,
        help="Specify a previous tests output directory with which the output "
        "of this test session is compared.",
    )
    parser.addoption(
        "--create_sample_output",
        action="store_true",
        default=False,
        help=(
            "During many of the tests, sample output is required to "
            "assess changes in the output files. This flag creates all "
            "of the required files for a future comparison and no "
            "comparison is made during the test session. "
        ),
    )
    parser.addoption(
        "--save_sample_output",
        action="store_true",
        default=False,
        help=(
            "By default, the afni_ci_test_data repository is used for "
            "all output data comparisons during testing. This flag "
            "updates the 'sample output' for each test run. Note that "
            "the output that is saved may be different from the output "
            "typically created because only files tested for "
            "differences are included though, by default, this is all "
            "files generated. If previous output exists, only the files "
            "that have differences, as defined by the tests, will be "
            "updated. Uploading updates to the publicly available "
            "repository must be done separately. "
        ),
    )

    parser.addoption(
        "--testpython2",
        action="store_true",
        help=(
            "For tests that use the python_interpreter fixture they are "
            "tested in both python 3 and python 2 "
        ),
    )


def pytest_collection_modifyitems(config, items):
    # more and more tests are skipped as each premature return is not executed:
    if config.getoption("--runveryslow"):
        # --runveryslow given in cli: do not skip slow tests
        return
    else:
        skip_veryslow = pytest.mark.skip(reason="need --runveryslow option to run")
        for item in items:
            if "veryslow" in item.keywords:
                item.add_marker(skip_veryslow)

    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_sessionfinish(session, exitstatus):
    output_directory = get_output_dir().absolute()
    print("\nTest output is written to: ", output_directory)

    if pytest.config.getoption("--create_sample_output") and not bool(exitstatus):
        print(
            "\n Sample output is written to:",
            tools.convert_to_sample_dir_path(get_output_dir()),
        )

    # When configured to save output and test session was successful...
    if pytest.config.getoption("--save_sample_output") and not bool(exitstatus):

        update_msg = "Update data with test run on {d}".format(
            d=datetime.datetime.today().strftime("%Y-%m-%d")
        )

        result = datalad.rev_save(
            get_base_comparison_dir_path(), update_msg, on_failure="stop"
        )

        sample_test_output = get_test_data_path() / "sample_test_output"
        data_message = (
            "New sample output was saved to {sample_test_output} for "
            "future comparisons. Consider publishing this new data to "
            "the publicly accessible servers.. "
        )
        print(data_message.format(**locals()))
    elif pytest.config.getoption("--save_sample_output"):
        print(
            "Sample output not saved because the test failed. You may "
            "want to clean this up with 'cd afni_ci_test_data;git reset "
            "--hard HEAD; git clean -df' \n Use this with caution though!"
        )