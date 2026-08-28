import asyncio
import json
import httpx
from app.core.config import settings
from app.integrations import fortyguard

TEST_POLYGONS = [
    {
        "name": "Abu Dhabi Downtown (Corniche/Reem)",
        "lat": 24.485,
        "lng": 54.365,
        "delta": 0.005,
    },
    {
        "name": "Abu Dhabi Yas Island",
        "lat": 24.498,
        "lng": 54.605,
        "delta": 0.005,
    },
    {
        "name": "Abu Dhabi Mussafah Industrial",
        "lat": 24.360,
        "lng": 54.500,
        "delta": 0.005,
    },
    {
        "name": "Dubai Downtown / Burj Khalifa",
        "lat": 25.197,
        "lng": 55.274,
        "delta": 0.005,
    },
    {
        "name": "Dubai Marina / JBR",
        "lat": 25.080,
        "lng": 55.140,
        "delta": 0.005,
    },
    {
        "name": "Phoenix Downtown AZ",
        "lat": 33.4484,
        "lng": -112.0740,
        "delta": 0.005,
    },
    {
        "name": "Los Angeles Downtown CA",
        "lat": 34.0407,
        "lng": -118.2468,
        "delta": 0.005,
    }
]

async def check_coverage():
    for site in TEST_POLYGONS:
        lat, lng, d = site["lat"], site["lng"], site["delta"]
        poly = {
            "type": "Polygon",
            "coordinates": [[
                [round(lng - d, 5), round(lat - d, 5)],
                [round(lng + d, 5), round(lat - d, 5)],
                [round(lng + d, 5), round(lat + d, 5)],
                [round(lng - d, 5), round(lat + d, 5)],
                [round(lng - d, 5), round(lat - d, 5)],
            ]]
        }
        print(f"\nTesting {site['name']} ({lat}, {lng})...")
        try:
            act_id = await fortyguard.submit_heat_query(poly, granularity=100)
            res = await fortyguard.poll_result(act_id)
            stats = res.get("data", {}).get("result", {}).get("stats_data", {})
            n_cells = stats.get("n_cells", 0)
            temp_stats = stats.get("temperature_stats", {})
            print(f"-> n_cells: {n_cells}, temp_stats: {temp_stats}")
            if n_cells > 0:
                print(f"-> SUCCESS! Found coverage: max={temp_stats.get('maximum')} C, mean={temp_stats.get('mean')} C")
                print("Full stats_data:", json.dumps(stats, indent=2))
                return site, stats
        except Exception as e:
            print(f"-> Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_coverage())
