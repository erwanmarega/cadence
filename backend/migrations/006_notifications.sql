create table if not exists public.notifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    type text not null,
    title text not null,
    body text,
    read boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists idx_notifications_user
    on public.notifications(user_id, created_at desc);

alter table public.notifications enable row level security;

create policy "own_notifications" on public.notifications
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

alter table public.goals
    add column if not exists notified_reached boolean not null default false;
