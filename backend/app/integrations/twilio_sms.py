"""Twilio SMS integration  -  sends heat alert SMS to workers as voice fallback."""

import re
import logging
from app.core.config import settings

from app.integrations.calle import format_e164, sanitize_api_key

logger = logging.getLogger(__name__)

MESSAGE_TEMPLATES: dict[str, str] = {
    "ur": "⚠️ {worker_name}, {site_name} par heat {temp}°F ho gaya hai. Bara-e-meherbani kaam rok kar shade mein chale jayein.",
    "en": "⚠️ {worker_name}, extreme heat ({temp}°F) detected at {site_name}. Please pause work and move to shade immediately.",
}


def send_sms(worker, site, snapshot) -> str:
    """Send an SMS alert to a worker with bilingual dynamic context. Returns Twilio message SID."""
    account_sid = sanitize_api_key(settings.twilio_account_sid)
    auth_token = sanitize_api_key(settings.twilio_auth_token)

    if not account_sid or not auth_token:
        raise ValueError("Twilio credentials not set. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env.")

    # Import here to avoid import error when Twilio is not needed
    from twilio.rest import Client

    client = Client(account_sid, auth_token)
    
    preferred_lang = getattr(worker, "preferred_language", "ur") or "ur"
    language = preferred_lang if preferred_lang in ("ur", "en") else "en"
    template = MESSAGE_TEMPLATES.get(language, MESSAGE_TEMPLATES["en"])
    
    temp_val = int(round(float(snapshot.temperature_f)))
    body = template.format(
        worker_name=worker.name,
        site_name=site.name,
        temp=temp_val,
        temperature_f=temp_val,
    )

    to_number = format_e164(worker.phone_number)
    from_number = format_e164(settings.twilio_from_number) if settings.twilio_from_number else settings.twilio_from_number

    logger.info(f"Sending Twilio SMS alert to '{worker.name}' ({to_number}), lang={language}")

    try:
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number,
        )
        logger.info(f"SMS sent successfully to {to_number}: sid={message.sid}")
        return message.sid
    except Exception as exc:
        logger.error(f"Twilio SMS send failed for worker '{worker.name}' ({to_number}): {exc}")
        raise
