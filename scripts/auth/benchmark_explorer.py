"""Measure synthetic static graphs; no input repository code is executed."""

import json
import platform
import statistics
import time
import tracemalloc
from pathlib import Path

from smartregression.adapters.parsers.javascript import parse_javascript
from smartregression.core.explorer.graph import build_graph, hotspots, impact, neighborhood


def main():
    measurements = []
    for size in [40, 150, 1000]:
        sources = {
            f"f{i}.js": ("" if i == 0 else f'import {{fn as previous}} from "./f{i - 1}.js";\n')
            + "export function fn(){"
            + ("return 1;" if i == 0 else "return previous();")
            + "}"
            for i in range(size)
        }
        tracemalloc.start()
        start = time.perf_counter()
        graph = build_graph("synthetic-benchmark", "a" * 40, sources, parse_javascript)
        build = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        timings = []
        for _ in range(5):
            start = time.perf_counter()
            selected = neighborhood(graph, limit=150)
            result = impact(graph, {"f0.js"})
            structural = hotspots(graph)
            timings.append(time.perf_counter() - start)
        assert len(selected.nodes) <= 150 and len(selected.edges) <= 1000
        assert len(result.direct) + len(result.indirect) == size - 1
        measurements.append(
            {
                "files": size,
                "source_bytes": sum(len(s.encode()) for s in sources.values()),
                "graph_nodes": len(graph.nodes),
                "graph_edges": len(graph.edges),
                "cold_build_seconds": build,
                "peak_traced_python_bytes": peak,
                "warm_combined_query_samples_seconds": timings,
                "warm_combined_query_median_seconds": statistics.median(timings),
                "path_proofs_returned": len(result.paths),
                "path_proofs_truncated": result.paths_truncated,
                "cycles": len(structural.cycles),
            }
        )
    target = Path(__file__).resolve().parents[2] / "var/phase3-8/explorer-benchmark.json"
    target.write_text(
        json.dumps(
            {
                "scope": "synthetic chain; static parsing only; no research accuracy claims",
                "python": platform.python_version(),
                "platform": platform.platform(),
                "processor": platform.processor(),
                "native_memory_limitations": "tracemalloc excludes native Tree-sitter allocations",
                "measurements": measurements,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Explorer benchmark measured and saved:", target)


if __name__ == "__main__":
    main()
