from fastapi.testclient import TestClient

from smartregression.api.main import create_app


def test_health_reports_service_only() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "schema_version": "1.0.0",
            "status": "ok",
            "service": "smartregression-api",
            "scope": "service_only",
        }


def test_analysis_and_demo_are_not_exposed() -> None:
    with TestClient(create_app()) as client:
        for path in ("/analyze", "/demo/report"):
            response = client.post(path)
            assert response.status_code == 404
            assert response.json()["code"] == "http_404"
