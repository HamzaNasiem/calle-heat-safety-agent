-- ThermaShift AI — Supabase / PostgreSQL Production Schema
-- Run this in your Supabase SQL editor (https://supabase.com/dashboard/project/_/sql)

create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ─────────────────────────────────────────
-- managers
-- ─────────────────────────────────────────
create table if not exists managers (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text unique not null,
  created_at timestamptz default now()
);
create index if not exists idx_managers_email on managers(email);

-- ─────────────────────────────────────────
-- sites
-- ─────────────────────────────────────────
create table if not exists sites (
  id uuid primary key default gen_random_uuid(),
  manager_id uuid references managers(id) on delete cascade,
  name text not null,
  polygon_geojson jsonb not null,          -- exact aoi, sent as-is to FortyGuard
  extreme_threshold_f numeric not null default 110,
  elevated_threshold_f numeric not null default 100,
  poll_interval_minutes int not null default 10,
  created_at timestamptz default now()
);
create index if not exists idx_sites_manager on sites(manager_id);
create index if not exists idx_sites_created on sites(created_at desc);

-- ─────────────────────────────────────────
-- workers
-- ─────────────────────────────────────────
create table if not exists workers (
  id uuid primary key default gen_random_uuid(),
  site_id uuid references sites(id) on delete cascade,
  name text not null,
  phone_number text not null,
  preferred_language text not null default 'en',   -- 'en', 'ur', etc.
  consented_at timestamptz default now(),           -- null = not consented
  status text not null default 'safe'
    check (status in ('safe','elevated','notified','acknowledged')),
  created_at timestamptz default now()
);
create index if not exists idx_workers_site on workers(site_id);
create index if not exists idx_workers_site_consented on workers(site_id, consented_at);
create index if not exists idx_workers_created on workers(created_at desc);

-- ─────────────────────────────────────────
-- heat_snapshots
-- ─────────────────────────────────────────
create table if not exists heat_snapshots (
  id uuid primary key default gen_random_uuid(),
  site_id uuid references sites(id) on delete cascade,
  fortyguard_activity_id text,
  temperature_f numeric not null,
  analysis_layer text not null default 'snapshot' check (analysis_layer in ('snapshot','exceedance','persistence')),
  risk_level text not null check (risk_level in ('normal','elevated','extreme')),
  raw_response jsonb,                        -- full FortyGuard response
  captured_at timestamptz default now()
);
create index if not exists idx_snapshots_site_time on heat_snapshots(site_id, captured_at desc);

-- ─────────────────────────────────────────
-- action_logs
-- ─────────────────────────────────────────
create table if not exists action_logs (
  id uuid primary key default gen_random_uuid(),
  worker_id uuid references workers(id) on delete cascade,
  heat_snapshot_id uuid references heat_snapshots(id) on delete set null,
  channel text not null check (channel in ('voice','sms')),
  provider_ref text,                          -- CALL-E call_id / Twilio sid
  status text not null default 'queued'
    check (status in ('queued','delivered','failed','acknowledged')),
  transcript text,
  created_at timestamptz default now(),
  constraint uq_worker_snapshot_channel unique (worker_id, heat_snapshot_id, channel)
);
create index if not exists idx_actionlogs_worker on action_logs(worker_id);
create index if not exists idx_actionlogs_snapshot on action_logs(heat_snapshot_id);
create index if not exists idx_actionlogs_created on action_logs(created_at desc);

-- ─────────────────────────────────────────
-- Seed Manager
-- ─────────────────────────────────────────
insert into managers (id, name, email) values
  ('00000000-0000-0000-0000-000000000001', 'ThermaShift Safety Operations', 'ops@thermashift.ai')
on conflict (id) do update set
  name = excluded.name,
  email = excluded.email;

-- ─────────────────────────────────────────
-- Seed Global Work Sites
-- ─────────────────────────────────────────
insert into sites (id, manager_id, name, polygon_geojson, extreme_threshold_f, elevated_threshold_f, poll_interval_minutes) values
  (
    '7eec064d-7724-49b9-b99f-9458017fa542',
    '00000000-0000-0000-0000-000000000001',
    'Abu Dhabi ICAD Heavy Industrial Yard, UAE',
    '{"type": "Polygon", "coordinates": [[[54.4881, 24.3272], [54.4961, 24.3272], [54.4961, 24.3352], [54.4881, 24.3352], [54.4881, 24.3272]]]}',
    112.0,
    102.0,
    10
  ),
  (
    '74e05dd1-39ae-449d-b894-729eb166edf8',
    '00000000-0000-0000-0000-000000000001',
    'Dubai Al Quoz Logistics & Construction Yard, UAE',
    '{"type": "Polygon", "coordinates": [[[55.2306, 25.1289], [55.2376, 25.1289], [55.2376, 25.1359], [55.2306, 25.1359], [55.2306, 25.1289]]]}',
    110.0,
    100.0,
    10
  ),
  (
    '4c417991-d47a-4f62-a82c-1a9e7aab65fb',
    '00000000-0000-0000-0000-000000000001',
    'Los Angeles Downtown Thermal Corridor, CA',
    '{"type": "Polygon", "coordinates": [[[-118.2498, 34.0377], [-118.2438, 34.0377], [-118.2438, 34.0437], [-118.2498, 34.0437], [-118.2498, 34.0377]]]}',
    105.0,
    96.0,
    10
  ),
  (
    '0bce18cc-6a3d-45db-b34b-e89491279632',
    '00000000-0000-0000-0000-000000000001',
    'Phoenix Sky Harbor Cargo & Freight Yard, AZ',
    '{"type": "Polygon", "coordinates": [[[-112.0141, 33.4312], [-112.0061, 33.4312], [-112.0061, 33.4392], [-112.0141, 33.4392], [-112.0141, 33.4312]]]}',
    114.0,
    104.0,
    10
  ),
  (
    'f6d5e1d6-15f8-4b1b-af71-aabb9df179be',
    '00000000-0000-0000-0000-000000000001',
    'Fresno Solar & Ag Field, Central Valley, CA',
    '{"type": "Polygon", "coordinates": [[[-119.7766, 36.7428], [-119.7686, 36.7428], [-119.7686, 36.7508], [-119.7766, 36.7508], [-119.7766, 36.7428]]]}',
    108.0,
    100.0,
    10
  )
on conflict (id) do update set
  name = excluded.name,
  polygon_geojson = excluded.polygon_geojson,
  extreme_threshold_f = excluded.extreme_threshold_f,
  elevated_threshold_f = excluded.elevated_threshold_f,
  poll_interval_minutes = excluded.poll_interval_minutes;

-- ─────────────────────────────────────────
-- Seed Workers (11 Crew Members Across 5 Sites)
-- ─────────────────────────────────────────
insert into workers (id, site_id, name, phone_number, preferred_language, consented_at, status) values
  ('11111111-1111-1111-1111-111111111111', '7eec064d-7724-49b9-b99f-9458017fa542', 'Rashid Al-Mansoor (Site Foreman)', '+923172532350', 'en', now(), 'safe'),
  ('11111111-1111-1111-1111-111111111112', '7eec064d-7724-49b9-b99f-9458017fa542', 'Zubair Khan (Crane Lead)', '+971501234567', 'ur', now(), 'safe'),
  ('11111111-1111-1111-1111-111111111113', '7eec064d-7724-49b9-b99f-9458017fa542', 'Ahmed Farooq (Welding Tech)', '+971509876543', 'ur', now(), 'safe'),
  ('22222222-2222-2222-2222-222222222222', '74e05dd1-39ae-449d-b894-729eb166edf8', 'Tariq Mehmood (Safety Officer)', '+923172532350', 'en', now(), 'safe'),
  ('22222222-2222-2222-2222-222222222223', '74e05dd1-39ae-449d-b894-729eb166edf8', 'Bilal Saeed (Concrete Crew)', '+971551122334', 'ur', now(), 'safe'),
  ('33333333-3333-3333-3333-333333333333', '4c417991-d47a-4f62-a82c-1a9e7aab65fb', 'Carlos Rodriguez (Civil Supervisor)', '+12135550192', 'en', now(), 'safe'),
  ('33333333-3333-3333-3333-333333333334', '4c417991-d47a-4f62-a82c-1a9e7aab65fb', 'Miguel Santos (Paving Tech)', '+12135550148', 'en', now(), 'safe'),
  ('44444444-4444-4444-4444-444444444444', '0bce18cc-6a3d-45db-b34b-e89491279632', 'David Martinez (Ground Ops)', '+16025550183', 'en', now(), 'safe'),
  ('44444444-4444-4444-4444-444444444445', '0bce18cc-6a3d-45db-b34b-e89491279632', 'John Miller (Loading Lead)', '+16025550174', 'en', now(), 'safe'),
  ('55555555-5555-5555-5555-555555555555', 'f6d5e1d6-15f8-4b1b-af71-aabb9df179be', 'Hamza (Field Operations Lead)', '+923172532350', 'en', now(), 'safe'),
  ('55555555-5555-5555-5555-555555555556', 'f6d5e1d6-15f8-4b1b-af71-aabb9df179be', 'Elena Morales (Harvest Lead)', '+15595550199', 'en', now(), 'safe')
on conflict (id) do update set
  name = excluded.name,
  phone_number = excluded.phone_number,
  preferred_language = excluded.preferred_language;
