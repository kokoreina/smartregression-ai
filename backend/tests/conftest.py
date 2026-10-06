import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def demo_path() -> Path:
    return ROOT / "examples/reports/demo.json"


@pytest.fixture
def demo_data(demo_path: Path) -> dict:
    return json.loads(demo_path.read_text(encoding="utf-8"))
