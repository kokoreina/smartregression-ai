import pytest

from smartregression.core.execution.config import ExecutionConfig


@pytest.mark.parametrize("field", ["timeout_seconds", "cpu_count", "memory_mib", "output_bytes"])
@pytest.mark.parametrize("value", [0, -1, True, float("inf"), float("nan")])
def test_invalid_limits_are_rejected(field, value):
    with pytest.raises(ValueError):
        ExecutionConfig(**{field: value})


@pytest.mark.parametrize(
    "path",
    ["../tests", "/tests", "C:/tests", "tests\\unit", "tests//unit", "./tests", "tests\nunit"],
)
def test_paths_cannot_escape_or_change_meaning(path):
    with pytest.raises(ValueError):
        ExecutionConfig(test_paths=(path,))


@pytest.mark.parametrize(
    "args", [("-c", "evil.ini"), ("-p", "evil"), ("--rootdir=/host",), (";whoami",)]
)
def test_repository_cannot_supply_arbitrary_pytest_arguments(args):
    with pytest.raises(ValueError):
        ExecutionConfig(approved_args=args)


def test_config_has_fixed_command_and_stable_hash():
    first, second = ExecutionConfig(), ExecutionConfig()
    assert first.fingerprint == second.fingerprint
    assert first.command == ("python", "-m", "pytest")
    assert ExecutionConfig(timeout_seconds=10).fingerprint != first.fingerprint
