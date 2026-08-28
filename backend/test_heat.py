"""Integration test for heat microclimate and hourly forecast endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_heat_endpoints():
    """Verify microclimate and hourly forecast endpoints for seeded sites."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sites_res = await client.get("/sites")
        assert sites_res.status_code == 200
        sites = sites_res.json()
        assert len(sites) >= 1
        site_id = sites[0]["id"]

        r1 = await client.get(f"/heat/microclimate?site_id={site_id}")
        assert r1.status_code == 200
        micro_data = r1.json()
        assert "ambient_temp_f" in micro_data
        assert "surface_temp_f" in micro_data
        assert "microcells" in micro_data
        assert len(micro_data["microcells"]) == 36

        r2 = await client.get(f"/heat/hourly-forecast?site_id={site_id}")
        assert r2.status_code == 200
        fc_data = r2.json()
        assert "points" in fc_data
        assert len(fc_data["points"]) == 10

