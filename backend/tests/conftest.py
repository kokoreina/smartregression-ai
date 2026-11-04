import importlib.util
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


@pytest.fixture
def stage_artifacts() -> dict:
    return json.loads((ROOT / "examples/reports/stage-report.partial.json").read_text("utf-8"))


@pytest.fixture(scope="session")
def mapping_inputs():
    # Load the task-owned helper without depending on console pytest adding the
    # project root or a generic "fixtures" package to sys.path.
    helper = Path(__file__).parent / "fixtures/mapping_inputs.py"
    spec = importlib.util.spec_from_file_location("mapping_fixture_inputs", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.mapping_inputs
