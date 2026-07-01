create table if not exists public.goals (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    base text not null,
    quote_currency text not null default 'EUR',
    target_amount numeric not null check (target_amount > 0),
    title text,
    created_at timestamptz not null default now()
);

create index if not exists idx_goals_user on public.goals(user_id);

alter table public.goals enable row level security;

create policy "own_goals" on public.goals
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
