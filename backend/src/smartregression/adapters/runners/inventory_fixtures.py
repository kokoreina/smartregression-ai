"""Task-authored source data; only these exact byte sets may reach the fixture collector."""


def fixture_sources(case: str) -> dict[str, bytes]:
    good = b"def test_one():\n    raise RuntimeError('must_not_execute_test_body')\n"
    cases = {
        "success": {"tests/test_inventory.py": good},
        "empty": {"not_a_test.py": b"value = 1\n"},
        "failed": {"tests/test_broken.py": b"raise RuntimeError('owned_collection_error')\n"},
        "partial": {
            "tests/test_inventory.py": good,
            "tests/test_broken.py": b"raise RuntimeError('owned_collection_error')\n",
        },
        "duplicate": {
            "tests/test_inventory.py": good,
            "conftest.py": (
                b"def pytest_collection_modifyitems(items):\n    items.append(items[0])\n"
            ),
        },
        "timeout": {"conftest.py": b"import time\ntime.sleep(60)\n"},
        "output_limit": {"conftest.py": b"import os\nos.write(1, b'x' * 100000)\n"},
    }
    if case not in cases:
        raise ValueError("unknown_inventory_fixture")
    return dict(cases[case])


FIXTURE_CASES = ("success", "empty", "failed", "partial", "duplicate", "timeout", "output_limit")
