import pytest

from smartregression.core.impact.changed_components import compare_python


def compare(base, target, **kwargs):
    return compare_python(base, target, path="src/orders.py", **kwargs)


def symbols(records):
    return {r.symbol: r for r in records if r.kind not in {"file", "module"}}


def test_changed_method_has_two_locations_and_containing_class():
    old = "class Order:\n    def total(self):\n        return 1\n"
    new = "class Order:\n    def total(self):\n        return 2\n"
    records = symbols(compare(old, new))
    assert set(records) == {"Order", "Order.total"}
    assert records["Order.total"].kind == "method"
    assert records["Order.total"].reason == "content_changed"
    assert records["Order"].reason == "contains_changed_symbol"
    assert records["Order.total"].base_location.line_start == 2
    assert records["Order.total"].target_location.line_end == 3


def test_deleted_added_and_signature_changes():
    old = "def gone():\n    return 1\ndef keep(a):\n    return a\n"
    new = "def fresh():\n    return 2\ndef keep(a, b=0):\n    return a\n"
    records = symbols(compare(old, new))
    assert {name: r.change for name, r in records.items()} == {
        "fresh": "added",
        "gone": "deleted",
        "keep": "modified",
    }
    assert records["gone"].target_location is None
    assert records["fresh"].base_location is None


def test_relocation_does_not_modify_symbols_but_module_still_changes():
    source = "def same():\n    return 1\n"
    records = compare(source, "\n\n" + source)
    assert symbols(records) == {}
    assert [r.kind for r in records] == ["module"]


def test_module_level_change_and_comment_edit_are_visible():
    records = compare("import os\nVALUE = 1\n", "import sys\nVALUE = 2\n")
    assert len(records) == 1 and records[0].kind == "module"
    result = symbols(compare("def f():\n    return 1\n", "def f():\n    # note\n    return 1\n"))
    assert result["f"].reason == "content_changed"


def test_decorators_async_nested_and_same_name_methods():
    old = (
        "class A:\n    @old\n    async def run(self):\n        pass\n"
        "class B:\n    def run(self):\n        pass\n"
    )
    new = old.replace("@old", "@new")
    result = symbols(compare(old, new))
    assert set(result) == {"A", "A.run"}
    assert result["A.run"].base_location.line_start == 2
    nested = symbols(compare(None, "def outer():\n    def inner():\n        pass\n"))
    assert nested["outer.inner"].kind == "function"


def test_file_rename_does_not_modify_unchanged_symbols():
    code = "def f():\n    return 1\n"
    records = compare(code, code, previous_path="src/old.py")
    assert len(records) == 1
    assert records[0].change == "renamed"
    assert records[0].previous_path == "src/old.py"
    assert records[0].reason == "path_changed"


def test_rename_with_edit_preserves_old_path_and_source_locations():
    records = symbols(
        compare(
            "def f():\n    return 1\n", "\ndef f():\n    return 2\n", previous_path="src/old.py"
        )
    )
    assert records["f"].change == "modified"
    assert records["f"].previous_path == "src/old.py"
    assert records["f"].base_location.line_start == 1
    assert records["f"].target_location.line_start == 2


@pytest.mark.parametrize(
    "source,code",
    [
        ("def broken(", "python_parse_failed"),
        ("def f():\n    pass\ndef f():\n    pass\n", "ambiguous_symbol"),
        ("#" * 256001, "source_limit"),
    ],
    ids=["invalid-syntax", "duplicate-symbol", "size-limit"],
)
def test_invalid_source_is_explicit(source, code):
    with pytest.raises(ValueError, match=code):
        compare("", source)


def test_empty_file_and_unmodified_source():
    assert compare("", "") == ()
    result = compare(None, "")
    assert result[0].change == "added"
    assert result[0].target_location is None


def test_added_child_does_not_report_parent_as_directly_edited():
    old = "class A:\n    def one(self):\n        pass\n"
    new = old + "    def two(self):\n        pass\n"
    records = symbols(compare(old, new))
    assert records["A"].reason == "contains_changed_symbol"
    assert records["A.two"].change == "added"
    assert "A.one" not in records


@pytest.mark.parametrize(
    "separator",
    ["\u2028", "\u2029", "\u0085"],
    ids=["line-separator", "paragraph-separator", "next-line"],
)
def test_unicode_inside_literal_uses_physical_python_lines(separator):
    old = f"def f():\n    return '{separator}before'\n"
    new = f"def f():\n    return '{separator}after'\n"
    records = compare(old, new)
    assert records[0].base_location.line_end == 2
    assert records[0].target_location.line_end == 2
    assert symbols(records)["f"].change == "modified"


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"], ids=["lf", "crlf", "cr"])
def test_source_locations_follow_python_newlines(newline):
    source = newline.join(["def f():", "    return 1", ""])
    records = compare(None, source)
    assert records[0].target_location.line_end == 2
    assert symbols(records)["f"].target_location.line_end == 2


def test_spacing_between_methods_does_not_claim_a_changed_child():
    old = "class A:\n    def one(self):\n        pass\n    def two(self):\n        pass\n"
    new = old.replace("    def two", "\n    def two")
    records = symbols(compare(old, new))
    assert set(records) == {"A"}
    assert records["A"].reason == "content_changed"
