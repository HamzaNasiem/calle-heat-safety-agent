"""Thermal Gradient & Relocation Vector Physics Service.

Calculates:
- Spatial microclimate mesh generation across GeoJSON AOI polygons
- Urban Heat Island (UHI) surface vs ambient contrast
- Albedo and solar irradiance modeling per surface/zone
- Peak Hotspot (T_max) and Coolest Refuge (T_min) identification
- Haversine geodesic distance (meters)
- Forward compass bearing (degrees & 16-point cardinal direction)
- OSHA / ISO 7243 WBGT thermal strain reduction delta
- Autonomous relocation action directives
"""

import math
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from app.services.risk_engine import (
    calculate_wbgt,
    calculate_work_rest_ratio,
    calculate_hydration_rate,
    fahrenheit_to_celsius,
)
from app.schemas.heat_snapshot import MicrocellDetail


# 16-point cardinal compass rose
COMPASS_DIRECTIONS_16 = [
    "N", "NNE", "NE", "ENE",
    "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW",
    "W", "WNW", "NW", "NNW"
]

# Surface Albedo constants (fraction of solar radiation reflected)
ALBEDO_MAP = {
    "asphalt": 0.08,
    "concrete": 0.35,
    "soil": 0.25,
    "shaded_canopy": 0.15,
    "green_buffer": 0.20,
}

# Solar Radiation standard exposures (W/m²)
SOLAR_EXPOSURE_MAP = {
    "direct_sun": 860.0,
    "partial_shade": 340.0,
    "full_canopy_shade": 110.0,
}


@dataclass
class RelocationVector:
    origin_id: str
    origin_lat: float
    origin_lng: float
    origin_air_temp_f: float
    origin_surface_temp_f: float
    origin_wbgt_f: float
    origin_zone: str
    target_id: str
    target_lat: float
    target_lng: float
    target_air_temp_f: float
    target_surface_temp_f: float
    target_wbgt_f: float
    target_zone: str
    distance_meters: int
    cooling_delta_f: float
    wbgt_relief_f: float
    wbgt_strain_reduction_pct: float
    compass_bearing_deg: float
    compass_direction: str
    action_directive: str


def calculate_haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    """Calculate great-circle ground distance between two GPS coordinates in meters."""
    r_earth = 6371000.0  # Earth's mean radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return int(round(r_earth * c))


def calculate_compass_bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> Tuple[float, str]:
    """Calculate forward initial compass bearing from (lat1, lng1) to (lat2, lng2).

    Formula:
      θ = atan2( sin(Δlong)*cos(lat2), cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(Δlong) )
    Returns tuple of (bearing_degrees_0_to_360, cardinal_direction_str).
    """
    if abs(lat1 - lat2) < 1e-9 and abs(lng1 - lng2) < 1e-9:
        return 0.0, "N"

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lng2 - lng1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    theta = math.atan2(y, x)
    bearing_deg = (math.degrees(theta) + 360.0) % 360.0
    bearing_deg = round(bearing_deg, 1)

    # 16-point compass segment indexing (each segment spans 22.5°)
    idx = int(round(bearing_deg / 22.5)) % 16
    cardinal = COMPASS_DIRECTIONS_16[idx]

    return bearing_deg, cardinal


def extract_polygon_bounds(polygon_geojson: dict[str, Any]) -> Tuple[float, float, float, float]:
    """Extract bounding box (min_lat, max_lat, min_lng, max_lng) from GeoJSON Polygon."""
    coords = polygon_geojson.get("coordinates", [[]])[0]
    if len(coords) >= 4:
        lats = [c[1] for c in coords]
        lngs = [c[0] for c in coords]
        return min(lats), max(lats), min(lngs), max(lngs)
    # Default industrial yard bounds (e.g. ICAD, Abu Dhabi)
    return 24.3272, 24.3352, 54.4881, 54.4961


def generate_spatial_microclimate_grid(
    polygon_geojson: dict[str, Any],
    ambient_temp_f: float = 102.5,
    relative_humidity: float = 50.0,
    rows: int = 6,
    cols: int = 6,
) -> Tuple[List[MicrocellDetail], Optional[MicrocellDetail], Optional[MicrocellDetail]]:
    """Generate high-resolution microcells across the AOI polygon.

    Models:
    - Sector A (Rows 0-2, Cols 0-3): High-exposure asphalt loading bays (High solar irradiance)
    - Sector D (Rows 4-5, Cols 4-5): Covered hydration canopy & shaded refuge (Low solar irradiance)
    - Sector B / C: Concrete / Compacted soil with variable tree buffer shade

    Calculates exact WBGT, surface heat deltas, albedo, hydration rates, and work/rest cycles per cell.
    """
    min_lat, max_lat, min_lng, max_lng = extract_polygon_bounds(polygon_geojson)
    d_lat = (max_lat - min_lat) / rows
    d_lng = (max_lng - min_lng) / cols

    microcells: List[MicrocellDetail] = []
    cell_counter = 101

    hotspot_cell: Optional[MicrocellDetail] = None
    refuge_cell: Optional[MicrocellDetail] = None
    max_surface_temp = -999.0
    min_surface_temp = 999.0

    for r in range(rows):
        for c in range(cols):
            c_lat = round(min_lat + (r + 0.5) * d_lat, 6)
            c_lng = round(min_lng + (c + 0.5) * d_lng, 6)

            if r <= 2 and c <= 3:
                stype = "asphalt"
                sexposure = "direct_sun"
                solar_rad = SOLAR_EXPOSURE_MAP["direct_sun"]
                uhi_bump = 16.5 + (2 - r) * 1.5 + (3 - c) * 1.0
                cell_air_temp = ambient_temp_f + (2 - r) * 0.8
            elif r >= 4 and c >= 4:
                stype = "shaded_canopy"
                sexposure = "full_canopy_shade"
                solar_rad = SOLAR_EXPOSURE_MAP["full_canopy_shade"]
                uhi_bump = -8.0
                cell_air_temp = ambient_temp_f - 12.0
            elif (r >= 3 and c >= 4) or (r >= 4 and c >= 3):
                stype = "green_buffer"
                sexposure = "partial_shade"
                solar_rad = SOLAR_EXPOSURE_MAP["partial_shade"]
                uhi_bump = -2.0
                cell_air_temp = ambient_temp_f - 4.5
            else:
                stype = "concrete" if r % 2 == 0 else "soil"
                sexposure = "direct_sun" if c % 2 == 0 else "partial_shade"
                solar_rad = 720.0 if sexposure == "direct_sun" else 420.0
                uhi_bump = 8.5 if sexposure == "direct_sun" else 2.0
                cell_air_temp = ambient_temp_f + (1.0 if sexposure == "direct_sun" else -1.0)

            surface_temp = round(cell_air_temp + uhi_bump, 1)
            cell_air_temp = round(cell_air_temp, 1)
            cell_temp_c = round(fahrenheit_to_celsius(cell_air_temp), 1)

            # Compute WBGT and safety parameters for this microcell
            cell_wbgt_f, _ = calculate_wbgt(
                temperature_f=cell_air_temp,
                relative_humidity=relative_humidity,
                solar_irradiance=solar_rad,
            )
            work_rest = calculate_work_rest_ratio(cell_wbgt_f)
            hydration = calculate_hydration_rate(
                wbgt_f=cell_wbgt_f,
                temperature_f=cell_air_temp,
                relative_humidity=relative_humidity,
                solar_irradiance=solar_rad,
            )
            albedo = ALBEDO_MAP.get(stype, 0.20)
            surface_heat_delta = round(surface_temp - cell_air_temp, 1)

            mcell = MicrocellDetail(
                id=f"FG-{cell_counter}",
                row=r,
                col=c,
                lat=c_lat,
                lng=c_lng,
                temp_f=cell_air_temp,
                temp_c=cell_temp_c,
                surface_temp_f=surface_temp,
                surface_type=stype,
                solar_exposure=sexposure,
                solar_radiation_w_m2=solar_rad,
                wbgt_f=round(cell_wbgt_f, 1),
                surface_heat_delta_f=surface_heat_delta,
                albedo=albedo,
                hydration_l_hr=hydration,
                work_rest_cycle=work_rest.ratio_str,
                is_hotspot=False,
                is_refuge=False,
            )

            if surface_temp > max_surface_temp:
                max_surface_temp = surface_temp
                hotspot_cell = mcell

            if (stype == "shaded_canopy" or stype == "green_buffer") and surface_temp < min_surface_temp:
                min_surface_temp = surface_temp
                refuge_cell = mcell

            microcells.append(mcell)
            cell_counter += 1

    if hotspot_cell:
        hotspot_cell.is_hotspot = True
    if refuge_cell:
        refuge_cell.is_refuge = True

    return microcells, hotspot_cell, refuge_cell


def compute_thermal_relief_vector(
    hotspot_cell: MicrocellDetail,
    refuge_cell: MicrocellDetail,
    site_name: str = "",
) -> RelocationVector:
    """Calculate dynamic Thermal Relief Vector from Peak Hotspot (T_max) to Coolest Sector (T_min)."""
    dist_m = calculate_haversine_distance(
        hotspot_cell.lat, hotspot_cell.lng, refuge_cell.lat, refuge_cell.lng
    )
    bearing_deg, cardinal = calculate_compass_bearing(
        hotspot_cell.lat, hotspot_cell.lng, refuge_cell.lat, refuge_cell.lng
    )
    cooling_relief_f = round(hotspot_cell.surface_temp_f - refuge_cell.surface_temp_f, 1)
    wbgt_relief_f = round(max(0.0, hotspot_cell.wbgt_f - refuge_cell.wbgt_f), 1)

    # Reduction in WBGT thermal strain percentage
    if hotspot_cell.wbgt_f > 0:
        reduction_pct = round((wbgt_relief_f / hotspot_cell.wbgt_f) * 100.0, 1)
    else:
        reduction_pct = 42.0

    origin_zone = f"Zone A ({hotspot_cell.surface_type.replace('_', ' ').title()} Hotspot)"
    target_zone = f"Zone D ({refuge_cell.surface_type.replace('_', ' ').title()} Refuge)"

    directive = (
        f"Autonomous Directive: Shift workforce {dist_m}m {cardinal} ({bearing_deg}°) from "
        f"Zone A ({hotspot_cell.surface_temp_f}°F Asphalt) to Zone D Canopy "
        f"(-{cooling_relief_f}°F Relief, -{wbgt_relief_f}°F WBGT). "
        f"Reduces WBGT thermal strain by {reduction_pct}%."
    )

    return RelocationVector(
        origin_id=hotspot_cell.id,
        origin_lat=hotspot_cell.lat,
        origin_lng=hotspot_cell.lng,
        origin_air_temp_f=hotspot_cell.temp_f,
        origin_surface_temp_f=hotspot_cell.surface_temp_f,
        origin_wbgt_f=hotspot_cell.wbgt_f,
        origin_zone=origin_zone,
        target_id=refuge_cell.id,
        target_lat=refuge_cell.lat,
        target_lng=refuge_cell.lng,
        target_air_temp_f=refuge_cell.temp_f,
        target_surface_temp_f=refuge_cell.surface_temp_f,
        target_wbgt_f=refuge_cell.wbgt_f,
        target_zone=target_zone,
        distance_meters=dist_m,
        cooling_delta_f=cooling_relief_f,
        wbgt_relief_f=wbgt_relief_f,
        wbgt_strain_reduction_pct=reduction_pct,
        compass_bearing_deg=bearing_deg,
        compass_direction=cardinal,
        action_directive=directive,
    )
