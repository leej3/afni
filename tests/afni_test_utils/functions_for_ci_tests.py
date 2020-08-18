from pathlib import Path
import os
import subprocess as sp
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    import datalad.api as datalad

from afni_test_utils import container_execution


def check_git_config():
    set_default_git_config_if_containerize()
    # basic config for git for circleci, assuming everyone else has configured git...
    gituser = sp.check_output("git config user.name".split()).decode().strip()
    gitemail = sp.check_output("git config user.email".split()).decode().strip()
    if not gituser:
        raise EnvironmentError("Need to set git user name")
    if not gitemail:
        raise EnvironmentError("Need to set git user email")


def check_test_data_repo(test_data, ignore_dirty_data):

    if (test_data.pathobj / "test_data_version.txt").exists():
        # For circleci Make sure test data is checked out correctly
        test_data.repo.update_submodule(test_data.path)
    else:
        if test_data.repo.dirty and not ignore_dirty_data:
            print("checking if test data repo is dirty")
            raise ValueError(
                "The test data is in a dirty state. You should commit any changes, clean the repository, or run tests with the ignore-dirty-data flag"
            )


def set_default_git_config_if_containerize():
    if is_containerized():
        sp.check_output(
            "git config --global user.name 'AFNI CircleCI User'", shell=True
        )
        sp.check_output(
            "git config --global user.email johnleenimh+circlecigitconfig@gmail.com".split()
        )


def configure_parallelism(cmd_args, use_all_cores):
    # Configure testing parallelism
    NCPUS = sp.check_output("getconf _NPROCESSORS_ONLN".split()).decode().strip()
    if use_all_cores:
        # this requires pytest-parallel to work
        cmd_args += f" --workers {NCPUS}".split()
        os.environ["OMP_NUM_THREADS"] = "1"
    else:
        os.environ["OMP_NUM_THREADS"] = NCPUS

    return cmd_args


def add_coverage_args(cmd_args):
    cov_options = "--cov=targets_built --cov-report xml:$PWD/coverage.xml".split()
    cmd_args += cov_options
    return cmd_args


def get_container_dir():
    return Path("/opt/afni/src/tests")


def is_containerized():
    env_file = Path("/.dockerenv")
    cgroup_info = Path("/proc/1/cgroup")
    if env_file.exists() or cgroup_info.exists():
        return True
    # if env_file_exists or any(pat in cgroup_info for pat in ['lxb','docker']):
    else:
        return False


def configure_for_coverage(cmd_args, **kwargs):
    out_args = cmd_args.copy()
    if kwargs.get("coverage"):
        # This will run correctly if the build has performed using the
        # appropriate build flags to enable coverage.
        if not (kwargs.get("build_dir") or kwargs.get("reuse_build")):
            raise ValueError(
                "If you want to test coverage, use the --build-dir or --reuse-build options."
            )

        # check that the pytest-cov plugin is installed
        res = sp.run("pytest --help".split(), stdout=sp.PIPE, stderr=sp.STDOUT)
        if "coverage reporting" not in res.stdout.decode("utf-8"):
            raise EnvironmentError("It seems pytest is missing the pytest-cov plugin.")

        out_args = add_coverage_args(out_args)
        os.environ[
            "CXXFLAGS"
        ] = "-g -O0 -Wall -W -Wshadow -Wunused-variable -Wunused-parameter -Wunused-function -Wunused -Wno-system-headers -Wno-deprecated -Woverloaded-virtual -Wwrite-strings -fprofile-arcs -ftest-coverage"
        os.environ["CFLAGS"] = "-g -O0 -Wall -W -fprofile-arcs -ftest-coverage"
        os.environ["LDFLAGS"] = "-fprofile-arcs -ftest-coverage"

    return out_args


def get_test_cmd_args(**kwargs):

    if kwargs.get("file"):
        cmd_args = [kwargs["file"]]
    else:
        cmd_args = ["scripts"]

    cmd_args += "-r=Exs  --show-capture=no --tb=no --verbose -s".split()

    if kwargs.get("verbose"):
        cmd_args += " -vv --showlocals -r Esx".split()

    if kwargs.get("debug"):
        cmd_args.append("--pdb")

    if kwargs.get("filter_expr"):
        cmd_args.append(f"-k={kwargs['filter_expr']}")

    cmd_args += (kwargs.get("extra_args") or "").split()

    return cmd_args


def generate_cmake_command_as_required(tests_dir, args_dict):
    """
    When a build dir has been defined, check whether is empty or sensibly
    populated. Return a command for both situations
    """
    container_execution.check_build_directory(args_dict["build_dir"])
    cmd = f"cd {args_dict['build_dir']}"
    if not os.listdir(args_dict["build_dir"]):
        cmd += f";cmake -GNinja {tests_dir.parent}"
    return cmd
