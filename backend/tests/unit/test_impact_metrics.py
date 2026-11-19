"""Independent expected file counts for task 3.48; fixture code is never executed."""

import pytest

from smartregression.adapters.parsers.javascript import parse_javascript
from smartregression.core.explorer.graph import build_graph, impact, neighborhood


def graph(sources):
    return build_graph("impact-metrics-fixture", "a" * 40, sources, parse_javascript)


def test_duplicate_diamond_and_shortcut_use_unique_shortest_distance_groups():
    value = graph(
        {
            "changed.js": "export const value=1;",
            "left.js": 'import "./changed.js"; import "./changed.js";',
            "right.js": 'import "./changed.js";',
            "join.js": 'import "./left.js"; import "./right.js";',
            "shortcut.js": 'import "./join.js"; import "./changed.js";',
            "unrelated.js": "export const value=1;",
        }
    )
    result = impact(value, {"changed.js"})
    assert result.changed == ["changed.js"]
    assert result.direct == ["left.js", "right.js", "shortcut.js"]
    assert result.indirect == ["join.js"]
    assert result.counts == {"changed": 1, "direct": 3, "indirect": 1, "potential": 5}
    assert result.denominator == 6
    assert result.percentages == {
        "changed": 16.67,
        "direct": 50,
        "indirect": 16.67,
        "potential": 83.33,
    }


def test_multiple_changed_files_and_cycle_do_not_recount_changed_as_dependents():
    value = graph(
        {
            "a.js": 'import "./b.js";',
            "b.js": 'import "./a.js";',
            "c.js": 'import "./a.js"; import "./b.js";',
            "d.js": 'import "./c.js";',
        }
    )
    result = impact(value, {"a.js", "b.js"})
    assert result.direct == ["c.js"]
    assert result.indirect == ["d.js"]
    assert result.counts == {"changed": 2, "direct": 1, "indirect": 1, "potential": 4}
    assert result.percentages == {"changed": 50, "direct": 25, "indirect": 25, "potential": 100}


def test_partial_snapshot_excludes_unparsed_and_unsupported_from_denominator():
    value = graph(
        {
            "a.py": "def work():\n    pass\n",
            "b.py": "from a import work\n",
            "broken.py": "def invalid(\n",
            "README.md": "Documentation",
        }
    )
    result = impact(value, {"a.py", "broken.py", "README.md"})
    assert result.coverage.status == "partial"
    assert result.denominator == 2
    assert result.counts == {"changed": 1, "direct": 1, "indirect": 0, "potential": 2}
    assert result.percentages == {"changed": 50, "direct": 50, "indirect": 0, "potential": 100}
    assert result.unknown_changed_count == 2
    assert result.changed == ["README.md", "a.py", "broken.py"]


@pytest.mark.parametrize(
    "sources,changed",
    [
        ({}, set()),
        ({"README.md": "Documentation"}, {"README.md"}),
        ({"broken.py": "def invalid(\n"}, {"broken.py"}),
    ],
)
def test_zero_analyzed_files_has_no_percentage(sources, changed):
    result = impact(graph(sources), changed)
    assert result.denominator is None
    assert all(value is None for value in result.percentages.values())
    assert result.counts == {"changed": 0, "direct": 0, "indirect": 0, "potential": 0}
    assert result.unknown_changed_count == len(changed)


def test_empty_change_set_is_measured_zero_when_denominator_is_known():
    result = impact(graph({"a.py": "value=1\n"}), set())
    assert result.denominator == 1
    assert result.percentages == {"changed": 0, "direct": 0, "indirect": 0, "potential": 0}


def test_viewport_truncation_does_not_reduce_full_snapshot_metrics():
    sources = {"a.js": "export const value=1;"}
    sources.update({f"dependent{i}.js": 'import "./a.js";' for i in range(160)})
    value = graph(sources)
    assert neighborhood(value, limit=1).truncated
    result = impact(value, {"a.js"})
    assert result.denominator == 161
    assert result.counts == {"changed": 1, "direct": 160, "indirect": 0, "potential": 161}
    assert result.paths_truncated
    assert len(result.paths) == 150
    assert result.percentages["potential"] == 100


def test_nonexistent_selected_path_is_rejected_instead_of_counted_as_unknown():
    with pytest.raises(ValueError, match="unknown_changed_path"):
        impact(graph({"a.py": "value=1\n"}), {"not-in-snapshot.py"})
