"""Supabase client (service-role).

Service-role key bypasses RLS, so EVERY query in this backend must filter
by user_id explicitly. RLS remains the defense-in-depth layer for any
access path that uses the user's own token.
"""

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)
