"""Test common route patterns across all projects."""
import pytest

# Each project should have these basic list endpoints
PROJECT_LIST_ENDPOINTS = {
    "vi-home-one": ["/api/projects/vi-home-one/neighborhoods"],
    "bsh-home-connect": ["/api/projects/bsh-home-connect/devices"],
    "adtech-intelligence": [
        "/api/projects/adtech-intelligence/campaigns",
        "/api/projects/adtech-intelligence/inventory",
        "/api/projects/adtech-intelligence/issues",
    ],
    "mol-asm-cockpit": [
        "/api/projects/mol-asm-cockpit/stations/regions",
        "/api/projects/mol-asm-cockpit/stations",
    ],
}


class TestProjectListEndpoints:
    """All project list endpoints should return 200 with list data."""

    @pytest.mark.parametrize(
        "endpoint",
        [ep for eps in PROJECT_LIST_ENDPOINTS.values() for ep in eps],
    )
    def test_list_endpoint_returns_200(self, client, endpoint):
        resp = client.get(endpoint)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestProjectNotFound:
    """404 handling for all projects."""

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/projects/vi-home-one/households/99999",
            "/api/projects/bsh-home-connect/devices/99999",
            "/api/projects/adtech-intelligence/campaigns/99999",
            "/api/projects/mol-asm-cockpit/stations/99999",
        ],
    )
    def test_get_nonexistent_returns_404(self, client, endpoint):
        resp = client.get(endpoint)
        assert resp.status_code in (404, 422)
