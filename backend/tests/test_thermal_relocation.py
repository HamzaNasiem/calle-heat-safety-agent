"""Unit tests for Thermal Relocation Vector & Spatial Microclimate Grid Physics (thermal_relocation.py)."""

import math
import pytest

from app.services.thermal_relocation import (
    calculate_haversine_distance,
    calculate_compass_bearing,
    extract_polygon_bounds,
    generate_spatial_microclimate_grid,
    compute_thermal_relief_vector,
    COMPASS_DIRECTIONS_16,
)
from app.schemas.heat_snapshot import MicrocellDetail


def test_haversine_distance():
    """Verify great-circle distance calculation between GPS coordinates."""
    # Abu Dhabi ICAD Yard bounds: delta ~0.004 deg lat is ~444m
    lat1, lng1 = 24.3272, 54.4881
    lat2 = 24.3352
    lng2 = 54.4961

    dist = calculate_haversine_distance(lat1, lng1, lat2, lng2)
    assert 1100 <= dist <= 1300  # ~1190 meters diagonal

    # Zero distance for identical points
    assert calculate_haversine_distance(lat1, lng1, lat1, lng1) == 0


def test_compass_bearing():
    """Verify initial forward compass bearing calculation and cardinal direction mapping."""
    # Due North: lat increases, lng constant
    bearing_n, dir_n = calculate_compass_bearing(24.0, 54.0, 25.0, 54.0)
    assert bearing_n == 0.0 or bearing_n == 360.0 or round(bearing_n) == 0
    assert dir_n == "N"

    # Due East: lat constant, lng increases
    bearing_e, dir_e = calculate_compass_bearing(24.0, 54.0, 24.0, 55.0)
    assert 89.0 <= bearing_e <= 91.0
    assert dir_e in ("E", "ENE", "ESE")

    # Due South: lat decreases, lng constant
    bearing_s, dir_s = calculate_compass_bearing(25.0, 54.0, 24.0, 54.0)
    assert 179.0 <= bearing_s <= 181.0
    assert dir_s == "S"

    # Due West: lat constant, lng decreases
    bearing_w, dir_w = calculate_compass_bearing(24.0, 55.0, 24.0, 54.0)
    assert 269.0 <= bearing_w <= 271.0
    assert dir_w in ("W", "WSW", "WNW")

    # South-East vector: from (0, 0) to (-1, 1) or from (24.3352, 54.4881) to (24.3272, 54.4961)
    bearing_se, dir_se = calculate_compass_bearing(24.3352, 54.4881, 24.3272, 54.4961)
    assert 120.0 <= bearing_se <= 150.0
    assert dir_se in ("SE", "SSE", "ESE")


def test_extract_polygon_bounds():
    """Verify bounding box extraction from GeoJSON Polygon."""
    polygon = {
        "type": "Polygon",
        "coordinates": [[
            [54.4881, 24.3272],
            [54.4961, 24.3272],
            [54.4961, 24.3352],
            [54.4881, 24.3352],
            [54.4881, 24.3272],
        ]]
    }
    min_lat, max_lat, min_lng, max_lng = extract_polygon_bounds(polygon)
    assert min_lat == 24.3272
    assert max_lat == 24.3352
    assert min_lng == 54.4881
    assert max_lng == 54.4961


def test_generate_spatial_microclimate_grid():
    """Verify 6x6 spatial grid generation with accurate thermal zoning and microcell physics."""
    polygon = {
        "type": "Polygon",
        "coordinates": [[
            [54.4881, 24.3272],
            [54.4961, 24.3272],
            [54.4961, 24.3352],
            [54.4881, 24.3352],
            [54.4881, 24.3272],
        ]]
    }
    ambient_temp = 104.0
    microcells, hotspot, refuge = generate_spatial_microclimate_grid(
        polygon_geojson=polygon,
        ambient_temp_f=ambient_temp,
        relative_humidity=55.0,
        rows=6,
        cols=6,
    )

    # Exactly 36 microcells
    assert len(microcells) == 36

    # Hotspot cell is identified (Sector A asphalt)
    assert hotspot is not None
    assert hotspot.is_hotspot is True
    assert hotspot.surface_type == "asphalt"
    assert hotspot.surface_temp_f > ambient_temp
    assert hotspot.solar_radiation_w_m2 >= 800.0
    assert hotspot.wbgt_f > 85.0
    assert hotspot.hydration_l_hr >= 1.0

    # Refuge cell is identified (Sector D shaded canopy)
    assert refuge is not None
    assert refuge.is_refuge is True
    assert refuge.surface_type in ("shaded_canopy", "green_buffer")
    assert refuge.surface_temp_f < hotspot.surface_temp_f
    assert refuge.solar_radiation_w_m2 <= 350.0

    # Surface temperature difference is substantial
    assert hotspot.surface_temp_f - refuge.surface_temp_f >= 20.0


def test_compute_thermal_relief_vector():
    """Verify thermal relief vector calculation connecting peak hotspot to cooling refuge."""
    hotspot = MicrocellDetail(
        id="FG-101",
        row=0,
        col=0,
        lat=24.3280,
        lng=54.4890,
        temp_f=106.0,
        temp_c=41.1,
        surface_temp_f=128.5,
        surface_type="asphalt",
        solar_exposure="direct_sun",
        solar_radiation_w_m2=860.0,
        wbgt_f=94.2,
        surface_heat_delta_f=22.5,
        albedo=0.08,
        hydration_l_hr=1.45,
        work_rest_cycle="STOP_WORK",
        is_hotspot=True,
        is_refuge=False,
    )

    refuge = MicrocellDetail(
        id="FG-136",
        row=5,
        col=5,
        lat=24.3345,
        lng=54.4955,
        temp_f=92.0,
        temp_c=33.3,
        surface_temp_f=90.0,
        surface_type="shaded_canopy",
        solar_exposure="full_canopy_shade",
        solar_radiation_w_m2=110.0,
        wbgt_f=79.5,
        surface_heat_delta_f=-2.0,
        albedo=0.15,
        hydration_l_hr=0.75,
        work_rest_cycle="60/0",
        is_hotspot=False,
        is_refuge=True,
    )

    vector = compute_thermal_relief_vector(hotspot, refuge, site_name="ICAD Industrial")

    assert vector.origin_id == "FG-101"
    assert vector.target_id == "FG-136"
    assert vector.cooling_delta_f == round(128.5 - 90.0, 1)  # 38.5°F
    assert vector.wbgt_relief_f == round(94.2 - 79.5, 1)    # 14.7°F
    assert vector.distance_meters > 0
    assert 0.0 <= vector.compass_bearing_deg <= 360.0
    assert vector.compass_direction in COMPASS_DIRECTIONS_16
    assert vector.wbgt_strain_reduction_pct > 10.0
    assert "Autonomous Directive" in vector.action_directive
    assert f"-{vector.cooling_delta_f}°F" in vector.action_directive
