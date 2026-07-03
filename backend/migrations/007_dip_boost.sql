alter table public.strategies
    add column if not exists dip_enabled boolean not null default false,
    add column if not exists dip_pct numeric,
    add column if not exists dip_window integer,
    add column if not exists dip_multiplier numeric;
