import pytest

from smartregression.core.impact.python_snapshot import (
    changed_symbols,
    inspect_python,
    module_edges,
)


def test_import_edges_and_changed_symbols_are_snapshot_local():
    sources = {
        "calc.py": "def add(a,b):\n    return a+b\n",
        "tests/test_calc.py": "from calc import add\n",
    }
    assert module_edges(sources) == (("tests/test_calc.py", "calc.py"),)
    assert changed_symbols("def add(a,b):\n    return a-b\n", sources["calc.py"]) == ("add",)
    assert changed_symbols(sources["calc.py"], sources["calc.py"]) == ()


def test_symbols_include_decorators_nested_names_and_imports():
    result = inspect_python("import math\n@decorate\ndef total():\n    return math.ceil(1)\n")
    assert [(s.name, s.start, s.end) for s in result.symbols] == [("total", 2, 4)]
    assert result.imports == ("math",)
    assert result.limitations  # Import observations are not a complete dependency graph.


def test_syntax_failure_is_not_empty_success():
    with pytest.raises(ValueError, match="python_parse_failed"):
        inspect_python("def broken(")


def test_dynamic_and_relative_imports_are_explicitly_partial():
    result = inspect_python('from . import sibling\n__import__("plugin")\n')
    assert "relative_import_unresolved" in result.limitations
    assert "dynamic_import" in result.limitations


def test_nested_qualified_symbols():
    result = inspect_python("class A:\n    async def work(self):\n        pass\n")
    assert [s.name for s in result.symbols] == ["A", "A.work"]
