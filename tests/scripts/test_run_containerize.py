from unittest.mock import MagicMock, patch, Mock
from collections import namedtuple
import os
import subprocess as sp
from pathlib import Path
import pytest
from argparse import Namespace
import sys

TESTS_DIR = Path(__file__).parent.parent

from afni_test_utils import container_execution


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
    container_execution.run_containerized(
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
        container_execution.run_containerized(
            TESTS_DIR, **{"image_name": "unknown_image", "only_use_local": True,}
        )


def test_setup_docker_env_and_vol_settings():
    # basic usage
    container_execution.setup_docker_env_and_vol_settings(TESTS_DIR,)

    # Confirm source directory is mounted
    source_dir, *_ = container_execution.get_path_strs_for_mounting(TESTS_DIR)
    docker_kwargs = container_execution.setup_docker_env_and_vol_settings(
        TESTS_DIR, **{"source_mode": "host"},
    )
    assert docker_kwargs.get("volumes").get(source_dir)
    expected = "/opt/afni/build,/opt/user_pip_packages"
    assert docker_kwargs.get("environment")["CHOWN_EXTRA"] == expected
    assert docker_kwargs["environment"].get("CONTAINER_UID")

    # Confirm test-data directory is mounted
    _, data_dir, *_ = container_execution.get_path_strs_for_mounting(TESTS_DIR)
    docker_kwargs = container_execution.setup_docker_env_and_vol_settings(
        TESTS_DIR, **{"source_mode": "test-data-only"},
    )
    assert docker_kwargs.get("volumes").get(data_dir)
    expected = "/opt/afni/src/tests/afni_ci_test_data"
    assert docker_kwargs.get("environment")["CHOWN_EXTRA"] == expected
    assert not docker_kwargs["environment"].get("CONTAINER_UID")

    # Confirm tests directory is mounted and file permissions is set correctly
    _, data_dir, *_ = container_execution.get_path_strs_for_mounting(TESTS_DIR)
    docker_kwargs = container_execution.setup_docker_env_and_vol_settings(
        TESTS_DIR, **{"source_mode": "test-code"},
    )
    assert docker_kwargs.get("volumes").get(str(TESTS_DIR))
    expected = "/opt/afni/install,/opt/user_pip_packages"
    assert docker_kwargs.get("environment")["CHOWN_EXTRA"] == expected
    assert docker_kwargs["environment"].get("CONTAINER_UID")

    # Confirm build directory is mounted
    _, data_dir, *_ = container_execution.get_path_strs_for_mounting(TESTS_DIR)
    docker_kwargs = container_execution.setup_docker_env_and_vol_settings(
        TESTS_DIR, **{"build_dir": data_dir},
    )
    assert docker_kwargs.get("volumes").get(data_dir)
    assert not docker_kwargs["environment"].get("CONTAINER_UID")
    