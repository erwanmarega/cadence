alter table public.trades
    add column if not exists source text not null default 'cadence' check (source in ('cadence','exchange')),
    add column if not exists side text check (side in ('buy','sell')),
    add column if not exists ext_id text,
    add column if not exists exchange text;

alter table public.trades alter column strategy_id drop not null;

create unique index if not exists uniq_trades_user_ext
    on public.trades(user_id, ext_id) where ext_id is not null;
