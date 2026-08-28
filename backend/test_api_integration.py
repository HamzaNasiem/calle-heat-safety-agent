"""
Integration test suite for ThermaShift AI FastAPI endpoints against local PostgreSQL database.
"""

import os
os.environ["ENVIRONMENT"] = "testing"

import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from app.core.config import settings
settings.environment = "testing"

from app.core.database import engine
from app.main import app

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(autouse=True)
async def cleanup_engine():
    """Dispose engine connections after each test to reset connection pool."""
    from app.core.database import init_db
    from seed_global_sites import seed_sites
    await init_db()
    await seed_sites()
    yield
    await engine.dispose()


def get_target_site(sites: list) -> dict:
    """Safely get the seeded site or fallback to last site."""
    for s in sites:
        if "Phoenix" in s.get("name", ""):
            return s
    return sites[-1]


async def test_health_endpoint():
    """Verify liveness health check endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "ThermaShift AI"


async def test_list_sites_endpoint():
    """Verify listing work sites from PostgreSQL database."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/sites")
        assert response.status_code == 200
        sites = response.json()
        assert isinstance(sites, list)
        assert len(sites) >= 1
        site = sites[0]
        assert "id" in site
        assert "name" in site
        assert "polygon_geojson" in site
        assert "extreme_threshold_f" in site
        assert "elevated_threshold_f" in site


async def test_get_site_by_id_endpoint():
    """Verify retrieving a specific site by ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sites_res = await client.get("/sites")
        assert sites_res.status_code == 200
        sites = sites_res.json()
        site_id = sites[0]["id"]

        response = await client.get(f"/sites/{site_id}")
        assert response.status_code == 200
        site = response.json()
        assert site["id"] == site_id


async def test_create_site_endpoint():
    """Verify creating a new site in PostgreSQL database."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sites_res = await client.get("/sites")
        assert sites_res.status_code == 200
        existing_site = sites_res.json()[0]
        manager_id = existing_site["manager_id"]

        payload = {
            "name": "QA Test Site",
            "polygon_geojson": {
                "type": "Polygon",
                "coordinates": [[
                    [-112.08, 33.445],
                    [-112.07, 33.445],
                    [-112.07, 33.455],
                    [-112.08, 33.455],
                    [-112.08, 33.445]
                ]]
            },
            "extreme_threshold_f": 110.0,
            "elevated_threshold_f": 100.0,
            "poll_interval_minutes": 15,
            "manager_id": manager_id
        }
        response = await client.post("/sites", json=payload)
        assert response.status_code == 201
        created = response.json()
        assert created["name"] == "QA Test Site"
        assert created["poll_interval_minutes"] == 15


async def test_list_workers_endpoint():
    """Verify listing workers for a given site from PostgreSQL."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sites_res = await client.get("/sites")
        assert sites_res.status_code == 200
        sites = sites_res.json()
        target_site = get_target_site(sites)
        site_id = target_site["id"]

        response = await client.get(f"/workers?site_id={site_id}")
        assert response.status_code == 200
        workers = response.json()
        assert isinstance(workers, list)
        assert len(workers) >= 1
        worker = workers[0]
        assert "id" in worker
        assert "name" in worker
        assert "phone_number" in worker
        assert "status" in worker


async def test_create_worker_endpoint():
    """Verify enrolling a new worker in PostgreSQL."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sites_res = await client.get("/sites")
        assert sites_res.status_code == 200
        sites = sites_res.json()
        target_site = get_target_site(sites)
        site_id = target_site["id"]

        payload = {
            "site_id": site_id,
            "name": "Test Worker QA",
            "phone_number": "+15005550006",
            "preferred_language": "en"
        }
        response = await client.post("/workers", json=payload)
        assert response.status_code == 201
        worker = response.json()
        assert worker["name"] == "Test Worker QA"
        assert worker["site_id"] == site_id
        assert worker["status"] == "safe"


async def test_get_worker_by_id_endpoint():
    """Verify getting a single worker by ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sites_res = await client.get("/sites")
        assert sites_res.status_code == 200
        sites = sites_res.json()
        target_site = get_target_site(sites)
        site_id = target_site["id"]

        workers_res = await client.get(f"/workers?site_id={site_id}")
        assert workers_res.status_code == 200
        worker_id = workers_res.json()[0]["id"]

        response = await client.get(f"/workers/{worker_id}")
        assert response.status_code == 200
        worker = response.json()
        assert worker["id"] == worker_id


async def test_get_heat_endpoint():
    """Verify getting the latest heat snapshot for a site."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sites_res = await client.get("/sites")
        assert sites_res.status_code == 200
        sites = sites_res.json()
        target_site = get_target_site(sites)
        site_id = target_site["id"]

        response = await client.get(f"/heat?site_id={site_id}")
        assert response.status_code == 200
        snapshot = response.json()
        assert "temperature_f" in snapshot
        assert "risk_level" in snapshot
        assert snapshot["site_id"] == site_id


async def test_get_heat_history_endpoint():
    """Verify getting heat snapshot history for a site."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sites_res = await client.get("/sites")
        assert sites_res.status_code == 200
        sites = sites_res.json()
        target_site = get_target_site(sites)
        site_id = target_site["id"]

        response = await client.get(f"/heat/history?site_id={site_id}&limit=5")
        assert response.status_code == 200
        history = response.json()
        assert isinstance(history, list)
        assert len(history) >= 1


async def test_list_alerts_endpoint():
    """Verify listing alert action logs for a site."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sites_res = await client.get("/sites")
        assert sites_res.status_code == 200
        sites = sites_res.json()
        target_site = get_target_site(sites)
        site_id = target_site["id"]

        response = await client.get(f"/alerts?site_id={site_id}&limit=10")
        assert response.status_code == 200
        alerts = response.json()
        assert isinstance(alerts, list)


async def test_trigger_check_force_extreme_endpoint():
    """Verify manual P0 trigger-check endpoint with force_extreme=true."""
    from unittest.mock import patch, AsyncMock
    with patch("app.services.notifier.calle.trigger_outbound_call", new_callable=AsyncMock) as mock_call, \
         patch("app.services.notifier.twilio_sms.send_sms") as mock_sms:
        mock_call.return_value = "mock_call_integration_123"
        mock_sms.return_value = "mock_sms_integration_123"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            sites_res = await client.get("/sites")
            assert sites_res.status_code == 200
            sites = sites_res.json()
            target_site = get_target_site(sites)
            site_id = target_site["id"]

            response = await client.post(f"/internal/trigger-check?site_id={site_id}&force_extreme=true")
            assert response.status_code == 200
            data = response.json()
            assert data["risk_level"] == "extreme"
            assert data["temperature_f"] == 112.0
            assert data["alerts_dispatched"] is True
            assert "snapshot_id" in data


async def test_get_microclimate_endpoint():
    """Verify microclimate spatial grid and thermal relocation vector calculation endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sites_res = await client.get("/sites")
        assert sites_res.status_code == 200
        sites = sites_res.json()
        target_site = get_target_site(sites)
        site_id = target_site["id"]

        response = await client.get(f"/heat/microclimate?site_id={site_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["site_id"] == site_id
        assert "ambient_temp_f" in data
        assert "surface_temp_f" in data
        assert "cooling_delta_f" in data
        assert "recommended_shift_distance_m" in data
        assert "compass_bearing_deg" in data
        assert "compass_direction" in data
        assert "microcells" in data
        assert len(data["microcells"]) == 36
        assert "action_plan" in data
        assert "Autonomous Directive" in data["action_plan"]


async def test_get_hourly_forecast_endpoint():
    """Verify 10-hour diurnal thermal progression & WBGT forecast endpoint (09:00 - 18:00)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sites_res = await client.get("/sites")
        assert sites_res.status_code == 200
        sites = sites_res.json()
        target_site = get_target_site(sites)
        site_id = target_site["id"]

        response = await client.get(f"/heat/hourly-forecast?site_id={site_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["site_id"] == site_id
        assert "peak_hour" in data
        assert "peak_surface_temp_f" in data
        assert "points" in data
        assert len(data["points"]) == 10  # 09:00 to 18:00

        first_pt = data["points"][0]
        assert first_pt["hour"] == 9
        assert first_pt["time_label"] == "09:00 AM"
        assert "wbgt_f" in first_pt
        assert "work_rest_ratio" in first_pt
        assert "hydration_liters_per_hour" in first_pt
        assert first_pt["hydration_liters_per_hour"] >= 0.50


