import pytest

from smartregression.core.retrieval.exclusions import exclusion_reason


@pytest.mark.parametrize(
    "path,content,reason",
    [
        ("src/calc.py", b"def value():\n    return 1\n", None),
        ("src/keywords.py", b"keywords = {'PASSWORD': tokens.Keyword}\n", None),
        ("tests/test_calc.py", b"import calc\n", None),
        ("docs/guide.md", b"Local usage\n", None),
        ("README.rst", b"Usage\r\n", None),
        (".env", b"SYNTHETIC=fixture\n", "forbidden_path"),
        ("src/.ENV.local.py", b"value=1\n", "forbidden_path"),
        ("secrets/config.py", b"value=1\n", "forbidden_path"),
        ("vendor/example.py", b"value=1\n", "forbidden_path"),
        ("results/full_suite.json", b"{}", "evaluation_data"),
        ("docs/fault_labels.md", b"fixture\n", "evaluation_data"),
        ("src/labels.py", b"fixture=1\n", "evaluation_data"),
        ("docs/notes.md", b'{"reference_outcomes": [1]}', "evaluation_content"),
        ("src/config.py", b'password = "synthetic-fixture-only"\n', "recognized_secret"),
        ("docs/key.md", b"-----BEGIN PRIVATE KEY-----\nsynthetic\n", "recognized_secret"),
        ("src/blob.py", b"x\x00y", "unsupported_content"),
        ("docs/bad.md", b"\xff", "unsupported_content"),
        ("archive.zip", b"fixture", "unsupported_path"),
        ("other/notes.txt", b"fixture", "unsupported_path"),
    ],
)
def test_allowed_sources_and_whole_file_exclusions(path, content, reason):
    assert exclusion_reason(path, content) == reason


@pytest.mark.parametrize("path", ["../escape.py", "/absolute.py", "x\\escape.py"])
def test_unsafe_paths_rejected(path):
    with pytest.raises(ValueError):
        exclusion_reason(path, b"value=1")
