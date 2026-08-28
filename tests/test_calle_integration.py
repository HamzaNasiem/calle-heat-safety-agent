"""Test Suite for CALL-E Heat Safety Dispatcher & Agent Skill."""

import pytest
from skills.heat_safety_dispatcher.dispatcher import (
    HeatSafetyPayload,
    format_e164,
    build_dispatch_prompt,
    trigger_heat_call,
    DEFAULT_CALLE_API_KEY,
    DEFAULT_CALLE_BASE_URL,
)


def test_format_e164_validations():
    """Verify phone formatting conforms strictly to E.164."""
    assert format_e164("+12135550192") == "+12135550192"
    assert format_e164("2135550192") == "+12135550192"
    assert format_e164("12135550192") == "+12135550192"
    assert format_e164("+92 317 2532350") == "+923172532350"
    assert format_e164("+971-50-123-4567") == "+971501234567"


def test_build_dispatch_prompt_content():
    """Verify generated prompt contains all safety, OSHA, and acknowledgment directives."""
    payload = HeatSafetyPayload(
        phone_number="+12135550192",
        worker_name="Carlos Rodriguez",
        site_name="Downtown LA Logistics Hub",
        temperature_f=109.5,
        work_rest_ratio="15 min work / 45 min rest",
        hydration_liters_per_hour=1.5,
        cooling_refuge_direction="North-East Canopy (Sector B)",
    )
    prompt = build_dispatch_prompt(payload)

    assert "Downtown LA Logistics Hub" in prompt
    assert "Carlos Rodriguez" in prompt
    assert "109.5°F" in prompt
    assert "15 min work / 45 min rest" in prompt
    assert "1.5 Liters" in prompt
    assert "North-East Canopy (Sector B)" in prompt
    assert "Do you confirm and acknowledge" in prompt


@pytest.mark.asyncio
async def test_trigger_heat_call_live_or_mock():
    """Test actual dispatch call creation payload and response parsing with safe mock."""
    from unittest.mock import patch, MagicMock
    import httpx

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "call_id": "call_test_mock_123456",
        "status": "queued",
        "data": {"call_id": "call_test_mock_123456", "status": "queued"}
    }
    mock_resp.raise_for_status.return_value = None

    payload = HeatSafetyPayload(
        phone_number="+923172532350",
        worker_name="Hamza (Safety Lead)",
        site_name="Test Validation Facility",
        temperature_f=107.0,
    )

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await trigger_heat_call(payload=payload)
        assert result.call_id == "call_test_mock_123456"
        assert result.phone_number == "+923172532350"
        assert result.status in ("queued", "in-progress", "completed", "created")
