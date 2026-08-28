"""CALL-E (HeyCall-E) Voice AI Integration.
Dispatches real autonomous voice phone calls with dynamic task prompts,
structured acknowledgment schema, and live transcript tracking.
"""

import re
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def sanitize_url(url: str) -> str:
    """Sanitize URL by stripping whitespace, carriage returns, newlines, and trailing slashes."""
    if not url:
        return ""
    return re.sub(r"[\r\n\s]+", "", str(url)).rstrip("/")


def sanitize_api_key(key: str) -> str:
    """Sanitize API key by stripping whitespace, carriage returns, and newlines."""
    if not key:
        return ""
    return re.sub(r"[\r\n\s]+", "", str(key))


def format_e164(phone: str) -> str:
    """Format and validate phone number to standard E.164 (+[country code][digits]).
    
    Strips whitespace, line breaks, hyphens, parentheses, and other non-digit noise.
    Validates digit count to be between 7 and 15 digits according to ITU-T E.164.
    """
    if not phone:
        raise ValueError("Phone number cannot be empty")
    cleaned_input = str(phone).strip().replace("\r", "").replace("\n", "")
    if not cleaned_input:
        raise ValueError("Phone number cannot be empty")
    
    digits_only = re.sub(r"\D", "", cleaned_input)
    if not digits_only:
        raise ValueError(f"Phone number '{phone}' contains no valid digits")
    
    if len(digits_only) < 7 or len(digits_only) > 15:
        raise ValueError(
            f"Phone number '{phone}' must contain between 7 and 15 digits (E.164 standard), got {len(digits_only)}"
        )
    return f"+{digits_only}"


def build_task_prompt(to_number: str, worker_name: str, site_name: str, temp_f_str: str, language: str = "en") -> str:
    """Construct professional English task instruction for CALL-E voice agent."""
    return (
        f"Call {to_number} and immediately speak in fluent, professional, authoritative English to worker {worker_name}. "
        f"Deliver this urgent OSHA heat safety broadcast: "
        f"'Attention {worker_name}! This is the CALL-E Heat Guardian autonomous heat safety dispatcher. "
        f"A critical thermal hazard of {temp_f_str} degrees Fahrenheit has been recorded at your work site, {site_name}. "
        f"Under OSHA safety protocol, you are required to immediately halt heavy outdoor tasks, move to the shaded cooling canopy, and hydrate with cool water.' "
        f"Ask {worker_name} if they understand and confirm they are moving to shade."
    )


async def trigger_outbound_call(worker, site, snapshot) -> str:
    """Trigger a real CALL-E outbound call to a worker with professional English task instructions
    and structured verification schema.
    Returns the call_id (e.g. 'call_91-GpTzKXNBvpPox8NN4gw').
    """
    api_key = sanitize_api_key(settings.calle_api_key)
    base_url = sanitize_url(settings.calle_base_url)
    if not api_key:
        raise ValueError("CALLE_API_KEY is not configured in .env")

    to_number = format_e164(worker.phone_number)
    language = "en"
    temp_f_str = str(int(round(float(snapshot.temperature_f))))

    task_instruction = build_task_prompt(to_number, worker.name, site.name, temp_f_str, "en")

    payload = {
        "task": task_instruction,
        "result_schema": {
            "type": "object",
            "required": ["worker_acknowledged"],
            "properties": {
                "worker_acknowledged": {
                    "type": "boolean",
                    "description": "Whether the worker confirmed hearing the heat evacuation warning"
                }
            },
            "additionalProperties": False
        },
        "metadata": {
            "worker_id": str(worker.id),
            "worker_name": worker.name,
            "site_id": str(site.id),
            "site_name": site.name,
            "temperature_f": float(snapshot.temperature_f),
            "risk_level": str(snapshot.risk_level),
            "language": language,
            "system": "CALL-E Heat Guardian",
        }
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    logger.info(f"Triggering CALL-E voice call to {worker.name} ({to_number}), temp={temp_f_str}°F")

    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(
            f"{base_url}/calls",
            json=payload,
            headers=headers,
        )

        # Fallback to English if regional language was rejected
        if resp.status_code == 422:
            logger.warning(f"CALL-E rejected regional prompt, retrying with universal English prompt for {to_number}...")
            payload["task"] = build_task_prompt(to_number, worker.name, site.name, temp_f_str, "en")
            resp = await client.post(
                f"{base_url}/calls",
                json=payload,
                headers=headers,
            )

        if resp.status_code >= 400:
            logger.error(f"CALL-E API Error ({resp.status_code}): {resp.text}")
        resp.raise_for_status()

        data = resp.json()
        call_id = data.get("id") or data.get("call_id", "")
        logger.info(f"CALL-E voice call queued successfully: call_id={call_id} -> {to_number}")
        return call_id


async def get_call_status(call_id: str) -> dict:
    """Fetch live call execution status, structured result, and summary from CALL-E."""
    api_key = sanitize_api_key(settings.calle_api_key)
    base_url = sanitize_url(settings.calle_base_url)
    if not api_key:
        raise ValueError("CALLE_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{base_url}/calls/{call_id.strip()}", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def get_call_events(call_id: str) -> dict:
    """Fetch live event log and transcript snippets from CALL-E."""
    api_key = sanitize_api_key(settings.calle_api_key)
    base_url = sanitize_url(settings.calle_base_url)
    if not api_key:
        raise ValueError("CALLE_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{base_url}/calls/{call_id.strip()}/events", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def trigger_direct_call(phone_number: str, worker_name: str) -> str:
    """Trigger a direct CALL-E call to any phone number with a standard heat-safety message.
    No DB worker or site required — used for demo/testing via DirectCallModal.
    Returns the call_id.
    """
    api_key = sanitize_api_key(settings.calle_api_key)
    base_url = sanitize_url(settings.calle_base_url)
    if not api_key:
        raise ValueError("CALLE_API_KEY is not configured in .env")

    to_number = format_e164(phone_number)

    task_instruction = (
        f"Call {to_number} and immediately speak in fluent, professional, authoritative English. "
        f"Say: 'Hello {worker_name}, this is a live test of the CALL-E Heat Guardian autonomous voice safety system. "
        f"If this were a real emergency, your work site would be reporting a critical thermal hazard and you would "
        f"be instructed to stop work and move to a shaded cooling area immediately. "
        f"This call confirms your emergency voice alert is working correctly.' "
        f"Ask {worker_name} if they received the test alert clearly."
    )

    payload = {
        "task": task_instruction,
        "result_schema": {
            "type": "object",
            "required": ["received_clearly"],
            "properties": {
                "received_clearly": {
                    "type": "boolean",
                    "description": "Whether the recipient confirmed the test alert was received"
                }
            },
            "additionalProperties": False,
        },
        "metadata": {
            "worker_name": worker_name,
            "phone_number": to_number,
            "call_type": "direct_test",
            "system": "CALL-E Heat Guardian",
        },
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    logger.info(f"Triggering direct CALL-E test call to {worker_name} ({to_number})")

    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(f"{base_url}/calls", json=payload, headers=headers)

        if resp.status_code >= 400:
            logger.error(f"CALL-E direct call error ({resp.status_code}): {resp.text}")
        resp.raise_for_status()

        data = resp.json()
        call_id = data.get("id") or data.get("call_id", "")
        logger.info(f"CALL-E direct call queued: call_id={call_id} -> {to_number}")
        return call_id

