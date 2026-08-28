"""Interactive CLI Runner for CALL-E Heat Guardian.

Usage:
  python main.py --phone +1234567890 --worker "Carlos Rodriguez" --temp 108.5 --site "Downtown LA"
  python main.py --test
"""

import argparse
import asyncio
import sys
import os

# Add parent directories to path for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from skills.heat_safety_dispatcher.dispatcher import (
    HeatSafetyPayload,
    trigger_heat_call,
    poll_call_status,
)
from apps.python.calle-heat-guardian.config import settings


async def run_cli():
    parser = argparse.ArgumentParser(description="CALL-E Heat Safety Autonomous Voice Dispatcher")
    parser.add_argument("--phone", type=str, default=settings.default_test_phone, help="Worker E.164 phone number")
    parser.add_argument("--worker", type=str, default="Hamza (Safety Officer)", help="Worker or supervisor name")
    parser.add_argument("--site", type=str, default="Los Angeles Downtown Thermal Corridor, CA", help="Job site name")
    parser.add_argument("--temp", type=float, default=108.5, help="Measured surface/ground temperature (°F)")
    parser.add_argument("--ratio", type=str, default="15 min work / 45 min rest", help="OSHA work/rest schedule")
    parser.add_argument("--water", type=float, default=1.5, help="Hydration quota in Liters/hour")
    parser.add_argument("--direction", type=str, default="North-East Shaded Canopy (Sector B)", help="Cooling refuge direction")
    parser.add_argument("--test", action="store_true", help="Run quick test dispatch to default phone")

    args = parser.parse_args()

    payload = HeatSafetyPayload(
        phone_number=args.phone,
        worker_name=args.worker,
        site_name=args.site,
        temperature_f=args.temp,
        work_rest_ratio=args.ratio,
        hydration_liters_per_hour=args.water,
        cooling_refuge_direction=args.direction,
    )

    print("=" * 65)
    print("🚨 CALL-E Heat Guardian — Autonomous Emergency Voice Dispatcher")
    print("=" * 65)
    print(f"Target Recipient : {payload.worker_name} ({payload.phone_number})")
    print(f"Job Site Location: {payload.site_name}")
    print(f"Hazardous Temp   : {payload.temperature_f}°F (Extreme Heat Level)")
    print(f"Mandated Break   : {payload.work_rest_ratio}")
    print(f"Hydration Quota  : {payload.hydration_liters_per_hour} L/hr")
    print(f"Cooling Refuge   : {payload.cooling_refuge_direction}")
    print("-" * 65)
    print("📞 Dialing outbound phone call via CALL-E Voice AI API...")

    try:
        result = await trigger_heat_call(
            payload=payload,
            api_key=settings.calle_api_key,
            base_url=settings.calle_base_url,
        )
        print("✅ Call Task Created Successfully!")
        print(f"   Call ID : {result.call_id}")
        print(f"   Status  : {result.status.upper()}")
        print(f"   Summary : {result.summary}")
        print("-" * 65)
        print("⏳ Polling CALL-E for live call completion and structured acknowledgment...")
        
        status_data = await poll_call_status(
            call_id=result.call_id,
            api_key=settings.calle_api_key,
            base_url=settings.calle_base_url,
            max_wait_seconds=30,
        )
        print(f"🎯 Final Call Status: {status_data.get('status', 'queued').upper()}")
        print("=" * 65)

    except Exception as exc:
        print(f"❌ Dispatch Error: {exc}")


if __name__ == "__main__":
    asyncio.run(run_cli())
