import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.models.manager import Manager
from app.models.site import Site
from app.models.worker import Worker
from app.models.heat_snapshot import HeatSnapshot
from app.models.action_log import ActionLog

DEFAULT_MANAGER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

GLOBAL_SITES = [
    {
        "id": uuid.UUID("4c417991-d47a-4f62-a82c-1a9e7aab65fb"),
        "name": "Los Angeles Downtown Thermal Corridor, CA",
        "lat": 34.0407,
        "lng": -118.2468,
        "delta": 0.003,
        "extreme_f": 105.0,
        "elevated_f": 96.0,
        "workers": [
            {"id": uuid.UUID("33333333-3333-3333-3333-333333333333"), "name": "Hamza (Safety Director)", "phone": "+12135550100", "lang": "en"},
            {"id": uuid.UUID("33333333-3333-3333-3333-333333333334"), "name": "Carlos Rodriguez (Civil Supervisor)", "phone": "+12135550192", "lang": "en"},
            {"id": uuid.UUID("33333333-3333-3333-3333-333333333335"), "name": "Miguel Santos (Paving Tech)", "phone": "+12135550148", "lang": "en"},
        ]
    },
    {
        "id": uuid.UUID("7eec064d-7724-49b9-b99f-9458017fa542"),
        "name": "Port of Los Angeles & Long Beach Terminal, CA",
        "lat": 33.7432,
        "lng": -118.2673,
        "delta": 0.0035,
        "extreme_f": 102.0,
        "elevated_f": 94.0,
        "workers": [
            {"id": uuid.UUID("11111111-1111-1111-1111-111111111111"), "name": "Hamza (Field Operations Lead)", "phone": "+13105550100", "lang": "en"},
            {"id": uuid.UUID("11111111-1111-1111-1111-111111111112"), "name": "James Thornton (Crane Lead)", "phone": "+13105550172", "lang": "en"},
            {"id": uuid.UUID("11111111-1111-1111-1111-111111111113"), "name": "Robert Chen (Container Tech)", "phone": "+13105550194", "lang": "en"},
        ]
    },
    {
        "id": uuid.UUID("f6d5e1d6-15f8-4b1b-af71-aabb9df179be"),
        "name": "Fresno Central Valley Solar & Ag Zone, CA",
        "lat": 36.7468,
        "lng": -119.7726,
        "delta": 0.004,
        "extreme_f": 108.0,
        "elevated_f": 100.0,
        "workers": [
            {"id": uuid.UUID("55555555-5555-5555-5555-555555555555"), "name": "Hamza (Solar Site Lead)", "phone": "+15595550100", "lang": "en"},
            {"id": uuid.UUID("55555555-5555-5555-5555-555555555556"), "name": "Elena Morales (Harvest Lead)", "phone": "+15595550199", "lang": "en"},
            {"id": uuid.UUID("55555555-5555-5555-5555-555555555557"), "name": "David Flores (Irrigation Tech)", "phone": "+15595550183", "lang": "en"},
        ]
    },
    {
        "id": uuid.UUID("74e05dd1-39ae-449d-b894-729eb166edf8"),
        "name": "Inland Empire Ontario Logistics Hub, CA",
        "lat": 34.0633,
        "lng": -117.6509,
        "delta": 0.0035,
        "extreme_f": 106.0,
        "elevated_f": 98.0,
        "workers": [
            {"id": uuid.UUID("22222222-2222-2222-2222-222222222222"), "name": "Hamza (Logistics Safety Lead)", "phone": "+19095550100", "lang": "en"},
            {"id": uuid.UUID("22222222-2222-2222-2222-222222222223"), "name": "Marcus Vance (Forklift Lead)", "phone": "+19095550141", "lang": "en"},
        ]
    },
    {
        "id": uuid.UUID("0bce18cc-6a3d-45db-b34b-e89491279632"),
        "name": "Silicon Valley San Jose Construction Yard, CA",
        "lat": 37.3382,
        "lng": -121.8863,
        "delta": 0.003,
        "extreme_f": 104.0,
        "elevated_f": 95.0,
        "workers": [
            {"id": uuid.UUID("44444444-4444-4444-4444-444444444444"), "name": "Hamza (Project Supervisor)", "phone": "+14085550100", "lang": "en"},
            {"id": uuid.UUID("44444444-4444-4444-4444-444444444445"), "name": "Brian Kelly (Structural Tech)", "phone": "+14085550198", "lang": "en"},
        ]
    }
]


def make_polygon(lat: float, lng: float, delta: float = 0.004) -> dict:
    """Create a rectangular GeoJSON Polygon around center coordinate."""
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [round(lng - delta, 4), round(lat - delta, 4)],
                [round(lng + delta, 4), round(lat - delta, 4)],
                [round(lng + delta, 4), round(lat + delta, 4)],
                [round(lng - delta, 4), round(lat + delta, 4)],
                [round(lng - delta, 4), round(lat - delta, 4)],
            ]
        ],
    }


async def seed_sites():
    """Seed default California industrial work sites, workers, and baseline heat snapshots."""
    async with AsyncSessionLocal() as session:
        # 1. Default Manager
        mgr = await session.get(Manager, DEFAULT_MANAGER_ID)
        if not mgr:
            mgr = Manager(
                id=DEFAULT_MANAGER_ID,
                name="CALL-E Enterprise Operations",
                email="ops@thermashift.ai",
            )
            session.add(mgr)
            await session.flush()

        for s_data in GLOBAL_SITES:
            # 2. Site
            site = await session.get(Site, s_data["id"])
            if not site:
                site = Site(
                    id=s_data["id"],
                    manager_id=DEFAULT_MANAGER_ID,
                    name=s_data["name"],
                    polygon_geojson=make_polygon(s_data["lat"], s_data["lng"], s_data["delta"]),
                    extreme_threshold_f=s_data["extreme_f"],
                    elevated_threshold_f=s_data["elevated_f"],
                    poll_interval_minutes=10,
                )
                session.add(site)
            else:
                site.name = s_data["name"]
                site.polygon_geojson = make_polygon(s_data["lat"], s_data["lng"], s_data["delta"])
                site.extreme_threshold_f = s_data["extreme_f"]
                site.elevated_threshold_f = s_data["elevated_f"]
            await session.flush()

            # 3. Workers
            for w_data in s_data["workers"]:
                worker = await session.get(Worker, w_data["id"])
                if not worker:
                    worker = Worker(
                        id=w_data["id"],
                        site_id=s_data["id"],
                        name=w_data["name"],
                        phone_number=w_data["phone"],
                        preferred_language=w_data["lang"],
                        status="safe",
                        consented_at=datetime.now(timezone.utc),
                    )
                    session.add(worker)
                else:
                    worker.name = w_data["name"]
                    worker.phone_number = w_data["phone"]
                    worker.preferred_language = w_data["lang"]
                    worker.consented_at = datetime.now(timezone.utc)
            await session.flush()

            # 4. Baseline Heat Snapshot
            snap_res = await session.execute(
                select(HeatSnapshot).where(HeatSnapshot.site_id == s_data["id"]).limit(1)
            )
            if not snap_res.scalars().first():
                snap = HeatSnapshot(
                    site_id=s_data["id"],
                    fortyguard_activity_id="seed-baseline",
                    temperature_f=round(s_data["elevated_f"] + 2.5, 1),
                    analysis_layer="snapshot",
                    risk_level="elevated",
                    raw_response={"seed": True, "temperature_f": s_data["elevated_f"] + 2.5},
                    captured_at=datetime.now(timezone.utc),
                )
                session.add(snap)

        await session.commit()
        print(f"Successfully seeded {len(GLOBAL_SITES)} California industrial sites with active heat coverage!")


if __name__ == "__main__":
    asyncio.run(seed_sites())
