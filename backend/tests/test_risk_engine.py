"""Unit tests for the OSHA & ISO 7243 Occupational Heat Safety Engine (risk_engine.py)."""

from datetime import datetime, timezone, timedelta
import pytest

from app.services.risk_engine import (
    RiskLevel,
    WorkloadCategory,
    fahrenheit_to_celsius,
    celsius_to_fahrenheit,
    calculate_stull_wet_bulb,
    calculate_globe_temperature,
    calculate_wbgt,
    calculate_work_rest_ratio,
    calculate_hydration_rate,
    classify_risk,
    classify_risk_with_persistence,
    assess_occupational_heat_risk,
)


def test_temperature_conversions():
    """Verify standard thermodynamic conversions between Fahrenheit and Celsius."""
    assert fahrenheit_to_celsius(32.0) == 0.0
    assert fahrenheit_to_celsius(212.0) == 100.0
    assert fahrenheit_to_celsius(104.0) == 40.0
    assert celsius_to_fahrenheit(0.0) == 32.0
    assert celsius_to_fahrenheit(100.0) == 212.0
    assert round(celsius_to_fahrenheit(40.0), 1) == 104.0


def test_stull_wet_bulb():
    """Verify Stull (2011) empirical natural wet-bulb equation accuracy."""
    # At 30°C and 50% RH, wet bulb is approximately 21-22°C
    twb = calculate_stull_wet_bulb(30.0, 50.0)
    assert 21.0 <= twb <= 23.0

    # At 40°C and 70% RH (high tropical heat/humidity), wet bulb is ~34-36°C
    twb_extreme = calculate_stull_wet_bulb(40.0, 70.0)
    assert 34.0 <= twb_extreme <= 36.5

    # At 0% relative humidity, Twb is lower than dry-bulb
    twb_dry = calculate_stull_wet_bulb(35.0, 5.0)
    assert twb_dry < 20.0


def test_globe_temperature():
    """Verify black globe temperature model under varying solar irradiance & wind speeds."""
    # At 35°C air temp, 800 W/m2 solar, 1 m/s wind -> Tg should be > 35°C
    tg = calculate_globe_temperature(35.0, solar_irradiance=800.0, wind_speed_m_s=1.0)
    assert tg > 35.0

    # Higher solar irradiance increases black globe heating
    tg_high_solar = calculate_globe_temperature(35.0, solar_irradiance=1200.0, wind_speed_m_s=1.0)
    assert tg_high_solar > tg

    # Zero solar irradiance (full shade) defaults to ambient dry bulb
    tg_shade = calculate_globe_temperature(35.0, solar_irradiance=0.0, wind_speed_m_s=2.0)
    assert tg_shade == 35.0


def test_calculate_wbgt():
    """Verify outdoor ISO 7243 WBGT calculation formula."""
    # 95°F, 50% RH, 800 W/m2 solar
    wbgt_f, wbgt_c = calculate_wbgt(95.0, relative_humidity=50.0, solar_irradiance=800.0)
    assert isinstance(wbgt_f, float)
    assert isinstance(wbgt_c, float)
    assert 82.0 <= wbgt_f <= 95.0
    assert 28.0 <= wbgt_c <= 35.0


def test_work_rest_ratios():
    """Verify OSHA & ISO 7243 work/rest ratio tiers for moderate workload."""
    # Continuous work under low WBGT (< 82.4°F)
    cycle_normal = calculate_work_rest_ratio(78.0)
    assert cycle_normal.ratio_str == "60/0"
    assert cycle_normal.work_minutes == 60
    assert cycle_normal.rest_minutes == 0

    # 50/10 cycle (elevated WBGT: 82.4°F - 86.0°F)
    cycle_elevated = calculate_work_rest_ratio(84.0)
    assert cycle_elevated.ratio_str == "50/10"
    assert cycle_elevated.work_minutes == 50
    assert cycle_elevated.rest_minutes == 10

    # 30/30 cycle (high WBGT: 86.0°F - 89.6°F)
    cycle_high = calculate_work_rest_ratio(88.0)
    assert cycle_high.ratio_str == "30/30"
    assert cycle_high.work_minutes == 30
    assert cycle_high.rest_minutes == 30

    # 15/45 cycle (severe WBGT: 89.6°F - 93.0°F)
    cycle_extreme = calculate_work_rest_ratio(91.5)
    assert cycle_extreme.ratio_str == "15/45"
    assert cycle_extreme.work_minutes == 15
    assert cycle_extreme.rest_minutes == 45

    # STOP WORK cycle (lethal WBGT: >= 93.0°F)
    cycle_stop = calculate_work_rest_ratio(94.5)
    assert cycle_stop.ratio_str == "STOP_WORK"
    assert cycle_stop.work_minutes == 0
    assert cycle_stop.rest_minutes == 60


def test_workload_category_adjustments():
    """Verify metabolic workload category offsets shift WBGT thresholds."""
    # Heavy workload lowers WBGT thresholds by 2.0°F
    cycle_heavy = calculate_work_rest_ratio(84.0, workload=WorkloadCategory.HEAVY)
    assert cycle_heavy.ratio_str == "30/30"

    # Very Heavy workload lowers WBGT thresholds by 4.0°F
    cycle_vheavy = calculate_work_rest_ratio(86.0, workload=WorkloadCategory.VERY_HEAVY)
    assert cycle_vheavy.ratio_str == "15/45"

    # Light workload increases tolerance by 2.0°F
    cycle_light = calculate_work_rest_ratio(83.0, workload=WorkloadCategory.LIGHT)
    assert cycle_light.ratio_str == "60/0"


def test_hydration_rate_bands():
    """Verify NIOSH / OSHA hydration rate scaling across Safe, Elevated, and Extreme tiers."""
    # Safe condition (< 90°F, low WBGT): 0.50 - 0.75 L/hr
    h_safe = calculate_hydration_rate(wbgt_f=70.0, temperature_f=75.0, relative_humidity=40.0, solar_irradiance=300.0)
    assert 0.50 <= h_safe <= 0.75

    # Elevated condition (90°F - 104.9°F, moderate WBGT): 0.75 - 1.00 L/hr
    h_elevated = calculate_hydration_rate(wbgt_f=85.0, temperature_f=96.0, relative_humidity=50.0, solar_irradiance=750.0)
    assert 0.75 <= h_elevated <= 1.10

    # Extreme condition (>= 105°F, high WBGT): 1.00 - 1.50 L/hr (capped at 1.50 L/hr)
    h_extreme = calculate_hydration_rate(wbgt_f=94.0, temperature_f=110.0, relative_humidity=65.0, solar_irradiance=950.0)
    assert 1.00 <= h_extreme <= 1.50


def test_classify_risk_osha_thresholds():
    """Verify risk classification against OSHA General Duty Clause thresholds:
    - Safe: < 90°F
    - Elevated: 90°F - 104.9°F
    - Extreme: >= 105°F
    """
    assert classify_risk(82.0) == RiskLevel.NORMAL
    assert classify_risk(90.0) == RiskLevel.ELEVATED
    assert classify_risk(98.5) == RiskLevel.ELEVATED
    assert classify_risk(104.5) == RiskLevel.ELEVATED
    assert classify_risk(105.0) == RiskLevel.EXTREME
    assert classify_risk(114.0) == RiskLevel.EXTREME


def test_classify_risk_wbgt_environmental_override():
    """Verify high solar radiation and humidity can elevate risk via WBGT calculation."""
    # 86°F with 85% RH and 900 W/m² solar -> WBGT > 82.4°F -> elevated
    level = classify_risk(86.0, relative_humidity=85.0, solar_irradiance=900.0)
    assert level == RiskLevel.ELEVATED

    # 98°F with 80% RH and 950 W/m² solar -> WBGT >= 89.6°F -> extreme
    level_ext = classify_risk(98.0, relative_humidity=80.0, solar_irradiance=950.0)
    assert level_ext == RiskLevel.EXTREME


def test_persistence_escalation():
    """Verify FortyGuard persistence layer elevates sustained elevated heat to extreme."""
    now = datetime.now(timezone.utc)

    # Elevated temperature for only 10 minutes -> remains ELEVATED
    elevated_recent = now - timedelta(minutes=10)
    level1 = classify_risk_with_persistence(
        temperature_f=98.0,
        elevated_threshold=90.0,
        extreme_threshold=105.0,
        elevated_since=elevated_recent,
        persistence_extreme_minutes=30,
        relative_humidity=40.0,
        solar_irradiance=500.0,
    )
    assert level1 == RiskLevel.ELEVATED

    # Elevated temperature sustained for 35 minutes -> escalates to EXTREME
    elevated_prolonged = now - timedelta(minutes=35)
    level2 = classify_risk_with_persistence(
        temperature_f=98.0,
        elevated_threshold=90.0,
        extreme_threshold=105.0,
        elevated_since=elevated_prolonged,
        persistence_extreme_minutes=30,
        relative_humidity=40.0,
        solar_irradiance=500.0,
    )
    assert level2 == RiskLevel.EXTREME


def test_full_safety_assessment():
    """Verify comprehensive safety assessment generation with all fields."""
    now = datetime.now(timezone.utc)
    elevated_since = now - timedelta(minutes=40)

    assessment = assess_occupational_heat_risk(
        temperature_f=95.0,
        relative_humidity=35.0,
        solar_irradiance=400.0,
        elevated_threshold=90.0,
        extreme_threshold=105.0,
        elevated_since=elevated_since,
        persistence_extreme_minutes=30,
        workload="moderate",
    )

    assert assessment.risk_level == RiskLevel.EXTREME
    assert assessment.persistence_escalated is True
    assert assessment.wbgt_f > 80.0
    assert assessment.work_rest_cycle.ratio_str in ("50/10", "30/30", "15/45", "STOP_WORK")
    assert 0.50 <= assessment.hydration_rate_l_hr <= 1.50
    assert assessment.escalation_reason is not None
    assert "persisted" in assessment.escalation_reason.lower()
