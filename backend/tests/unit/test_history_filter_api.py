"""Status filters are validated before reaching the data boundary."""

from backend.tests.unit.test_product_ownership_matrix import PROJECT, matrix_client  # noqa: F401


def test_history_rejects_unknown_status(matrix_client):  # noqa: F811 -- imported pytest fixture
    client, settings, boundary = matrix_client
    client.cookies.set(settings.session_cookie, "session-a")
    boundary._events.clear()
    response = client.get(f"/api/v1/projects/{PROJECT}/runs", params={"status": "partial"})
    assert response.status_code == 422
    assert boundary._events == []
