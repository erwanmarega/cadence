create extension if not exists "pgcrypto";

create table if not exists public.exchange_connections (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    exchange text not null check (exchange in ('kraken', 'coinbase')),
    api_key_enc text not null,
    api_secret_enc text not null,
    passphrase_enc text,
    api_key_hint text not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_exchange_connections_user
    on public.exchange_connections(user_id);

create table if not exists public.strategies (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    exchange_connection_id uuid not null
        references public.exchange_connections(id) on delete cascade,
    symbol text not null,
    amount numeric not null check (amount > 0),
    quote_currency text not null default 'EUR',
    interval text not null check (interval in ('daily','weekly','biweekly','monthly')),
    status text not null default 'active' check (status in ('active','paused')),
    next_run_at timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists idx_strategies_user on public.strategies(user_id);
create index if not exists idx_strategies_due
    on public.strategies(status, next_run_at);

create table if not exists public.trades (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    strategy_id uuid not null references public.strategies(id) on delete cascade,
    symbol text not null,
    amount numeric not null,
    quote_currency text not null,
    price numeric,
    filled numeric,
    status text not null check (status in ('success','failed')),
    error text,
    executed_at timestamptz not null default now()
);

create index if not exists idx_trades_user on public.trades(user_id);
create index if not exists idx_trades_strategy on public.trades(strategy_id);

alter table public.exchange_connections enable row level security;
alter table public.strategies enable row level security;
alter table public.trades enable row level security;

create policy "own_exchange_connections" on public.exchange_connections
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_strategies" on public.strategies
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "read_own_trades" on public.trades
    for select using (auth.uid() = user_id);
