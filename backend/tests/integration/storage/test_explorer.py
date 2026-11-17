"""Immutable graph/source caching and owner isolation, on real PostgreSQL."""

from contextlib import contextmanager

import pytest
from backend.tests.integration.storage.test_web_runs import runs  # noqa: F401 -- shared fixture
from backend.tests.unit.test_repository_web import TARGET, remote

from smartregression.adapters.parsers.javascript import parse_javascript
from smartregression.adapters.storage.explorer_store import PostgresExplorerStore
from smartregression.application.auth import AuthFailure
from smartregression.application.explorer import ExplorerService


@pytest.fixture
def explorer(request, tmp_path):
    service, user, stranger, project, projects, owner = request.getfixturevalue("runs")
    source = tmp_path / "explorer-source"
    source.mkdir()
    requests = []

    @contextmanager
    def factory(url):
        requests.append(url)
        value = remote(source)
        original = value._json

        def complete_tree(path):
            result = original(path)
            if "/git/trees/" in path:
                result["tree"].append(
                    {"path": "src", "type": "tree", "mode": "040000", "sha": "f" * 40}
                )
            return result

        value._json = complete_tree
        yield value

    store = PostgresExplorerStore(service.store.engine)
    return ExplorerService(store, factory, parse_javascript), user, stranger, project, requests


def test_materialize_readback_replay_and_bounded_source(explorer):
    service, user, _, project, requests = explorer
    value = service.materialize(user, project, TARGET)
    assert value.graph.commit == TARGET and value.tree.commit == TARGET
    assert service.materialize(user, project, TARGET) == value and len(requests) == 1
    assert service.source(user, project, TARGET, "app.py", 1, 5).content.startswith("from src.math")
    assert service.graph(user, project, TARGET, limit=1).truncated
    assert service.impact(user, project, TARGET, {"src/math.py"}).direct == ["app.py"]


def test_other_owner_cannot_materialize_read_graph_or_source(explorer):
    service, user, stranger, project, requests = explorer
    service.materialize(user, project, TARGET)
    for action in [
        lambda: service.materialize(stranger, project, TARGET),
        lambda: service.graph(stranger, project, TARGET),
        lambda: service.source(stranger, project, TARGET, "app.py", 1, 5),
    ]:
        with pytest.raises(AuthFailure) as error:
            action()
        assert error.value.status == 404
    assert len(requests) == 1
