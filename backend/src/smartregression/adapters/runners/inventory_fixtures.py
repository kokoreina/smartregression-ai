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
        "plugin_error": {
            "tests/test_inventory.py": good,
            "conftest.py": (
                b"def pytest_collection_finish(session):\n"
                b"    raise RuntimeError('owned_plugin_error')\n"
            ),
        },
        "missing_result": {"conftest.py": b"import os\nos._exit(0)\n"},
        "malformed_result": {
            "conftest.py": b"print('\\nSMARTREGRESSION_RESULT={not json}', flush=True)\n",
            "tests/test_inventory.py": good,
        },
        "unsupported_id": {
            "tests/test_inventory.py": good,
            "conftest.py": (
                b"def pytest_collection_modifyitems(items):\n    items[0]._nodeid = 'test\\0id'\n"
            ),
        },
        "native_ids": {
            "tests/test_inventory.py": (
                b"import pytest\n@pytest.mark.parametrize('value', range(4))\n"
                b"def test_native(value):\n    raise RuntimeError('must_not_execute_test_body')\n"
            ),
            "conftest.py": (
                "def pytest_collection_modifyitems(items):\n"
                "    ids = [' test[đ] ', 'test[é]', 'test[e\\u0301]', 'test_' + 'x' * 9000]\n"
                "    for item, nodeid in zip(items, ids):\n        item._nodeid = nodeid\n"
            ).encode(),
        },
    }
    if case not in cases:
        raise ValueError("unknown_inventory_fixture")
    return dict(cases[case])


FIXTURE_CASES = (
    "success",
    "empty",
    "failed",
    "partial",
    "duplicate",
    "timeout",
    "output_limit",
    "plugin_error",
    "missing_result",
    "malformed_result",
    "unsupported_id",
    "native_ids",
)
