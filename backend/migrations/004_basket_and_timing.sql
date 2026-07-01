alter table public.strategies
    add column if not exists allocations jsonb,
    add column if not exists run_hour smallint not null default 9 check (run_hour between 0 and 23),
    add column if not exists run_minute smallint not null default 0 check (run_minute between 0 and 59),
    add column if not exists run_weekday smallint check (run_weekday between 0 and 6),
    add column if not exists run_day_of_month smallint check (run_day_of_month between 1 and 28);

alter table public.strategies alter column symbol drop not null;
