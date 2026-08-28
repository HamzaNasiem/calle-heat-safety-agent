import asyncio
import json
import httpx
from app.core.config import settings
from app.integrations import fortyguard

async def run_live_test():
    print("API Key configured:", settings.fortyguard_api_key)
    
    print("\n--- TEST 1: fetch_api_usage() ---")
    try:
        usage = await fortyguard.fetch_api_usage()
        print("Usage result successfully received:")
        print(json.dumps(usage, indent=2))
    except Exception as e:
        print("fetch_api_usage failed:", e)

    print("\n--- TEST 2: submit_heat_query() + poll_result() for Abu Dhabi Site ---")
    polygon = {
        "type": "Polygon",
        "coordinates": [[
            [54.4881, 24.3272],
            [54.4961, 24.3272],
            [54.4961, 24.3352],
            [54.4881, 24.3352],
            [54.4881, 24.3272]
        ]]
    }
    try:
        raw_res = await fortyguard.get_site_temperature(polygon)
        print("Poll completed successfully! Raw response snippet:")
        print("Message/Status:", raw_res.get("message"), raw_res.get("data", {}).get("status"))
        stats_data = raw_res.get("data", {}).get("result", {}).get("stats_data", {})
        print("stats_data:", json.dumps(stats_data, indent=2))
        
        temp_f = fortyguard.extract_temperature(raw_res)
        print(f"Extracted Temp: {temp_f}°F")
    except Exception as e:
        print("get_site_temperature failed:", e)

    print("\n--- TEST 3: env_params ---")
    try:
        env_res = await fortyguard.get_env_params(latitude=24.3312, longitude=54.4921, temperature=42.5)
        print("Env params result:")
        print(json.dumps(env_res, indent=2)[:500])
    except Exception as e:
        print("get_env_params failed:", e)

if __name__ == "__main__":
    asyncio.run(run_live_test())
