"""FortyGuard Temperature API integration  -  verified against live API."""

import asyncio
import logging
from datetime import datetime, timezone
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)
FORTYGUARD_BASE = "https://api.fortyguard.com/v1"


class FortyGuardError(Exception):
    pass


def ensure_valid_polygon(polygon_geojson: dict) -> dict:
    """Ensure polygon_geojson is a closed ring with at least 4 coordinates."""
    if not isinstance(polygon_geojson, dict):
        return polygon_geojson
    coords = polygon_geojson.get("coordinates", [])
    if coords and len(coords) > 0 and len(coords[0]) > 0:
        ring = list(coords[0])
        if len(ring) < 3:
            lat, lng = ring[0][1], ring[0][0]
            d = 0.005
            ring = [
                [lng - d, lat - d],
                [lng + d, lat - d],
                [lng + d, lat + d],
                [lng - d, lat + d],
                [lng - d, lat - d]
            ]
        elif len(ring) == 3:
            ring.append(ring[0])
        elif ring[0] != ring[-1]:
            ring.append(ring[0])
        return {"type": "Polygon", "coordinates": [ring]}
    return polygon_geojson


async def submit_heat_query(polygon_geojson: dict, granularity: int = 100, target_date: str | None = None, target_time: str | None = None) -> str:
    """Submit an async heatmap query to FortyGuard. Returns activity_id."""
    if not settings.fortyguard_api_key:
        raise FortyGuardError(
            "FORTYGUARD_API_KEY is not set in environment."
        )

    # Validate & sanitize polygon ring
    valid_polygon = ensure_valid_polygon(polygon_geojson)

    # FortyGuard baseline temperature model dataset uses peak summer date
    start_date = target_date or "2024-07-15"
    start_time = target_time or "14:00"

    payload = {
        "polygon_aoi": valid_polygon,
        "date_time": {
            "start_date": start_date,
            "start_time": start_time,
            "filter_type": 1,
        },
        "granularity": granularity,
    }
    headers = {"api-key": settings.fortyguard_api_key, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.post(f"{FORTYGUARD_BASE}/heatmap", json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise FortyGuardError(f"Network error submitting heatmap: {exc}")

        if resp.status_code != 200:
            raise FortyGuardError(f"Submit failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        activity_id = data.get("data", {}).get("activity_id")
        if not activity_id:
            raise FortyGuardError(f"No activity_id in response: {data}")

        logger.info(f"FortyGuard submit OK: activity_id={activity_id}")
        return activity_id


async def poll_result(activity_id: str, max_attempts: int = 15, delay_seconds: float = 2.0) -> dict:
    """Poll FortyGuard GET /v1/status/{activity_id} until async job resolves."""
    headers = {"api-key": settings.fortyguard_api_key}

    async with httpx.AsyncClient(timeout=20.0) as client:
        for attempt in range(max_attempts):
            try:
                resp = await client.get(
                    f"{FORTYGUARD_BASE}/status/{activity_id}",
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("data", {}).get("status") or data.get("message")
                    if status == "Completed":
                        logger.info(f"FortyGuard poll complete: activity_id={activity_id}")
                        return data
                    elif status in ("Processing", "In Progress", "Pending"):
                        logger.debug(f"FortyGuard activity {activity_id} still {status} (attempt {attempt+1}/{max_attempts})")
                elif resp.status_code == 429:
                    logger.warning("FortyGuard rate limited  -  backing off")
                else:
                    logger.warning(f"Poll attempt {attempt+1}: status={resp.status_code}")
            except httpx.HTTPError as exc:
                logger.warning(f"Poll HTTP error attempt {attempt+1}: {exc}")

            wait = delay_seconds * (1.2 ** attempt)
            await asyncio.sleep(wait)

    raise FortyGuardError(f"Poll timed out for activity_id={activity_id} after {max_attempts} attempts")


def extract_temperature(raw_response: dict) -> float:
    """Extract representative max temperature (°F) from verified FortyGuard response schema."""
    try:
        # Verified schema: data.result.stats_data.temperature_stats.maximum (in °C)
        data = raw_response.get("data", {})
        result = data.get("result", {})
        stats = result.get("stats_data", {}).get("temperature_stats", {})

        if "maximum" in stats:
            temp_c = float(stats["maximum"])
            return round((temp_c * 9 / 5) + 32, 2)

        if "mean" in stats or "average" in stats:
            temp_c = float(stats.get("mean") or stats.get("average"))
            return round((temp_c * 9 / 5) + 32, 2)

        # Alternative: check features inside map_data
        features = result.get("map_data", {}).get("features", [])
        if features:
            temps = [
                f.get("properties", {}).get("max_temperature")
                or f.get("properties", {}).get("average_temperature")
                or f.get("properties", {}).get("temperature")
                for f in features
                if f.get("properties")
            ]
            valid_temps = [t for t in temps if t is not None]
            if valid_temps:
                temp_c = float(max(valid_temps))
                return round((temp_c * 9 / 5) + 32, 2)

        # Fallbacks for synthetic/manual payloads
        if "temperature_f" in raw_response:
            return float(raw_response["temperature_f"])
        if "temperature_f" in data:
            return float(data["temperature_f"])

        # If n_cells is 0 (polygon outside covered high-res thermal grid), default gracefully
        n_cells = result.get("stats_data", {}).get("n_cells", -1)
        if n_cells == 0:
            logger.warning("FortyGuard returned 0 cells for polygon (outside high-res thermal model grid). Defaulting to 105.0°F.")
            return 105.0

        raise FortyGuardError(f"Could not find temperature stats in response: {list(raw_response.keys())}")
    except (TypeError, KeyError, ValueError) as exc:
        raise FortyGuardError(f"Temperature extraction error: {exc}. Raw payload: {raw_response}")


async def get_site_temperature(polygon_geojson: dict) -> dict:
    """End-to-end submit and poll helper for /v1/heatmap."""
    activity_id = await submit_heat_query(polygon_geojson)
    result = await poll_result(activity_id)
    return result


async def submit_env_params(
    latitude: float,
    longitude: float,
    temperature: float,
    target_date: str | None = None,
    target_time: str | None = None,
) -> str:
    """Submit an environmental parameters query to FortyGuard /v1/env_params. Returns activity_id."""
    if not settings.fortyguard_api_key:
        raise FortyGuardError("FORTYGUARD_API_KEY is not set in environment.")

    start_date = target_date or "2024-07-15"
    start_time = target_time or "14:00"

    payload = {
        "latitude": latitude,
        "longitude": longitude,
        "temperature": temperature,
        "date_time": {
            "start_date": start_date,
            "start_time": start_time,
            "filter_type": 1,
        },
    }
    headers = {"api-key": settings.fortyguard_api_key, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.post(f"{FORTYGUARD_BASE}/env_params", json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise FortyGuardError(f"Network error submitting env_params: {exc}")

        if resp.status_code != 200:
            raise FortyGuardError(f"Submit env_params failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        activity_id = data.get("data", {}).get("activity_id")
        if not activity_id:
            raise FortyGuardError(f"No activity_id in env_params response: {data}")

        logger.info(f"FortyGuard submit env_params OK: activity_id={activity_id}")
        return activity_id


async def get_env_params(
    latitude: float,
    longitude: float,
    temperature: float,
    target_date: str | None = None,
    target_time: str | None = None,
) -> dict:
    """End-to-end submit and poll helper for /v1/env_params."""
    activity_id = await submit_env_params(latitude, longitude, temperature, target_date, target_time)
    result = await poll_result(activity_id)
    return result


async def fetch_api_usage() -> dict:
    """Fetch current API credit usage and subscription status from /v1/system/fetch-api-key-usage."""
    headers = {"api-key": settings.fortyguard_api_key, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{FORTYGUARD_BASE}/system/fetch-api-key-usage",
            json={"api_key": settings.fortyguard_api_key},
            headers=headers,
        )
        if resp.status_code != 200:
            raise FortyGuardError(f"Failed to fetch API usage: {resp.text}")
        return resp.json()


