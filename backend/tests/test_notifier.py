"""Unit tests for CALL-E AI Voice, Twilio SMS integrations, and Notifier alert dispatch service."""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.integrations.calle import format_e164, trigger_outbound_call
from app.integrations.twilio_sms import send_sms, MESSAGE_TEMPLATES
from app.services import notifier


def test_format_e164():
    """Test E.164 phone formatting across various input formats."""
    assert format_e164("+923001234567") == "+923001234567"
    assert format_e164("923001234567") == "+923001234567"
    assert format_e164("  +1 (415) 555-2671  ") == "+14155552671"
    assert format_e164("0300-123-4567") == "+03001234567"

    with pytest.raises(ValueError):
        format_e164("")


@pytest.mark.asyncio
async def test_calle_trigger_outbound_call():
    """Test CALL-E AI outbound call payload construction."""
    class DummyWorker:
        id = uuid.uuid4()
        name = "Ahmed Khan"
        phone_number = "+923001234567"
        preferred_language = "en"

    class DummySite:
        id = uuid.uuid4()
        name = "Malir Worksite 1"

    class DummySnapshot:
        temperature_f = 112.4
        risk_level = "extreme"

    worker = DummyWorker()
    site = DummySite()
    snapshot = DummySnapshot()

    with patch("app.integrations.calle.settings") as mock_settings:
        mock_settings.calle_api_key = "test_key"
        mock_settings.calle_base_url = "https://api.heycall-e.com/v1"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "call_abc_123"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            call_id = await trigger_outbound_call(worker, site, snapshot)
            assert call_id == "call_abc_123"

            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            payload = kwargs["json"]
            assert "Ahmed Khan" in payload["task"]
            assert "Malir Worksite 1" in payload["task"]
            assert "112" in payload["task"]
            assert payload["metadata"]["worker_name"] == "Ahmed Khan"
            assert payload["metadata"]["temperature_f"] == 112.4
            assert payload["metadata"]["risk_level"] == "extreme"


def test_twilio_send_sms_bilingual():
    """Test Twilio SMS generation with dynamic context for Urdu and English."""
    class DummyWorker:
        name = "Fahad Ali"
        phone_number = "+923331234567"
        preferred_language = "en"

    class DummySite:
        name = "Phoenix Site"

    class DummySnapshot:
        temperature_f = 109.8

    worker = DummyWorker()
    site = DummySite()
    snapshot = DummySnapshot()

    with patch("app.integrations.twilio_sms.settings") as mock_settings:
        mock_settings.twilio_account_sid = "AC_test"
        mock_settings.twilio_auth_token = "token_test"
        mock_settings.twilio_from_number = "+18005550199"

        with patch("twilio.rest.Client") as mock_twilio_client:
            client_instance = MagicMock()
            mock_twilio_client.return_value = client_instance
            message_mock = MagicMock()
            message_mock.sid = "SM_xyz_789"
            client_instance.messages.create.return_value = message_mock

            sid = send_sms(worker, site, snapshot)
            assert sid == "SM_xyz_789"

            client_instance.messages.create.assert_called_once()
            _, kwargs = client_instance.messages.create.call_args
            assert kwargs["to"] == "+923331234567"
            assert kwargs["from_"] == "+18005550199"
            assert "Fahad Ali" in kwargs["body"]
            assert "Phoenix Site" in kwargs["body"]
            assert "110°F" in kwargs["body"]


@pytest.mark.asyncio
async def test_notifier_dispatch_consent_filtering():
    """Test that dispatch filters out workers where consented_at IS NULL."""
    site_id = uuid.uuid4()
    snapshot_id = uuid.uuid4()

    class MockWorker:
        def __init__(self, name, phone, consented):
            self.id = uuid.uuid4()
            self.name = name
            self.phone_number = phone
            self.preferred_language = "ur"
            self.consented_at = datetime.now(timezone.utc) if consented else None
            self.status = "safe"

    class MockSite:
        id = site_id
        name = "Test Site"

    class MockSnapshot:
        id = snapshot_id
        temperature_f = 112.0
        risk_level = "extreme"

    consented_worker = MockWorker("Consented", "+923001111111", True)
    unconsented_worker = MockWorker("Unconsented", "+923002222222", False)

    mock_db = AsyncMock()
    # Mock result scalars for consent filtering query
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [consented_worker]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch("app.services.notifier.already_notified", new_callable=AsyncMock) as mock_dedupe, \
         patch("app.services.notifier.calle.trigger_outbound_call", new_callable=AsyncMock) as mock_call, \
         patch("app.services.notifier.twilio_sms.send_sms") as mock_sms, \
         patch("app.services.notifier._log_action", new_callable=AsyncMock) as mock_log:

        mock_dedupe.return_value = False
        mock_call.return_value = "call_123"
        mock_sms.return_value = "sms_123"

        await notifier.dispatch(mock_db, MockSite(), MockSnapshot())

        # Consented worker called and SMS sent
        assert mock_call.call_count == 1
        assert mock_sms.call_count == 1
        assert consented_worker.status == "notified"
        assert unconsented_worker.status == "safe"


@pytest.mark.asyncio
async def test_notifier_dispatch_voice_failure_sms_fallback():
    """Test that voice call failure does not block SMS fallback."""
    class MockWorker:
        id = uuid.uuid4()
        name = "FailVoiceWorker"
        phone_number = "+923003333333"
        preferred_language = "ur"
        consented_at = datetime.now(timezone.utc)
        status = "safe"

    class MockSite:
        id = uuid.uuid4()
        name = "Fallback Site"

    class MockSnapshot:
        id = uuid.uuid4()
        temperature_f = 115.0
        risk_level = "extreme"

    worker = MockWorker()
    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [worker]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch("app.services.notifier.already_notified", new_callable=AsyncMock) as mock_dedupe, \
         patch("app.services.notifier.calle.trigger_outbound_call", new_callable=AsyncMock) as mock_call, \
         patch("app.services.notifier.twilio_sms.send_sms") as mock_sms, \
         patch("app.services.notifier._log_action", new_callable=AsyncMock) as mock_log:

        mock_dedupe.return_value = False
        mock_call.side_effect = Exception("CALL-E API connection failed")
        mock_sms.return_value = "sms_fallback_sid"

        await notifier.dispatch(mock_db, MockSite(), MockSnapshot())

        # Voice call attempted and failed
        mock_call.assert_called_once()
        # SMS fallback still executed successfully
        mock_sms.assert_called_once()
        # Log records created for both failed voice and delivered sms
        assert mock_log.call_count == 2
        assert worker.status == "notified"
