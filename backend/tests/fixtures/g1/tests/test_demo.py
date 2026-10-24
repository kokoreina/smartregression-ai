"""Owned fixture for the G1 mechanics demonstration, not a benchmark repository."""


def test_ok():
    assert 2 + 3 == 5


def test_other():
    assert "snapshot".startswith("snap")
