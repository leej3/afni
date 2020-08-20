import sys
import os
import subprocess
import datalad.api as datalad
import logging

from afni_test_utils.functions_for_ci_tests import (
    get_test_cmd_args,
    configure_parallelism,
    check_git_config,
    check_test_data_repo,
    generate_cmake_command_as_required,
    configure_for_coverage,
)


def run_tests(tests_dir, **args_dict):

    if args_dict.get("abin"):
        sys.path.insert(0, args_dict["abin"])
        # Also needs to work for shell subprocesses
        os.environ["PATH"] = f"{args_dict['abin']}:{os.environ['PATH']}"

    test_data = datalad.Dataset(str(tests_dir / "afni_ci_test_data"))
    check_git_config()
    if test_data.repo:
        check_test_data_repo(
            test_data, ignore_dirty_data=args_dict.get("ignore_dirty_data")
        )

    cmd_args = get_test_cmd_args(**args_dict)
    cmd_args = configure_parallelism(cmd_args, args_dict.get("use_all_cores"))
    cmd_args = configure_for_coverage(cmd_args, **args_dict)
    if args_dict.get("build_dir"):
        cmd = generate_cmake_command_as_required(tests_dir, args_dict)
        cmd += f""";ARGS='{' '.join(x for x in cmd_args)}' ninja pytest"""
    else:
        cmd = f"""pytest {' '.join(x for x in cmd_args)}"""

    print(f"Executing: {cmd}")
    res = subprocess.run(cmd, shell=True)
    sys.exit(res.returncode)
