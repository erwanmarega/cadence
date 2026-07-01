alter table public.strategies
    add column if not exists consecutive_failures int not null default 0;

alter table public.strategies
    add column if not exists last_error text;

alter table public.strategies
    drop constraint if exists strategies_status_check;

alter table public.strategies
    add constraint strategies_status_check
    check (status in ('active', 'paused', 'error'));
