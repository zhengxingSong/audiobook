"""Tests for the FastAPI web application."""

from fastapi.testclient import TestClient

from audiobook.web import create_app


class TestWebApp:
    """Smoke tests for the web application factory."""

    def test_dashboard_root_returns_html(self) -> None:
        """The root endpoint should render the dashboard HTML shell."""
        client = TestClient(create_app())

        response = client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "dashboard-shell" in response.text
        assert "Audiobook Control Room" in response.text

    def test_jobs_page_returns_html(self) -> None:
        """Jobs page should render its HTML shell."""
        client = TestClient(create_app())

        response = client.get("/jobs")

        assert response.status_code == 200
        assert "Launch and monitor conversion runs." in response.text

    def test_voices_page_returns_html(self) -> None:
        """Voices page should render its HTML shell."""
        client = TestClient(create_app())

        response = client.get("/voices")

        assert response.status_code == 200
        assert "Curate the voices" in response.text

    def test_health_endpoint(self) -> None:
        """The health endpoint should report service metadata."""
        client = TestClient(create_app())

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "audiobook-web"
        assert data["active_jobs"] == 0

    def test_static_dashboard_assets_are_served(self) -> None:
        """Dashboard CSS should be reachable through the static mount."""
        client = TestClient(create_app())

        response = client.get("/static/dashboard.css")

        assert response.status_code == 200
        assert "dashboard-shell" in response.text

    def test_service_assets_are_served(self) -> None:
        """Service CSS should also be reachable."""
        client = TestClient(create_app())

        response = client.get("/static/service.css")

        assert response.status_code == 200
        assert ".service-shell" in response.text

    def test_api_root_lists_service_endpoints(self) -> None:
        """API root should advertise the main service surfaces."""
        client = TestClient(create_app())

        response = client.get("/api")

        assert response.status_code == 200
        data = response.json()
        assert data["endpoints"]["jobs"] == "/api/jobs"
        assert data["endpoints"]["voices"] == "/api/voices"

    def test_missing_job_returns_404(self) -> None:
        """Unknown jobs should return a 404 error."""
        client = TestClient(create_app())

        response = client.get("/api/jobs/missing-job")

        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"
