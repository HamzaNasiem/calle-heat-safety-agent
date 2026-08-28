import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import sys
sys.path.insert(0, '.')
from app.models.heat_snapshot import HeatSnapshot

async def run():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/thermashift')
    SessionLocal = sessionmaker(engine, class_=AsyncSession)
    async with SessionLocal() as session:
        res = await session.execute(select(HeatSnapshot).limit(1))
        snap = res.scalar_one_or_none()
        print(json.dumps(snap.raw_response) if snap else 'No data')

if __name__ == "__main__":
    import app.models  # load all models
    asyncio.run(run())

