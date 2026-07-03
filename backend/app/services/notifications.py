"""Notifications: in-app feed (always) + optional email (Resend, if configured).

Triggers: a DCA buy executed, a plan suspended after repeated failures, a
savings goal reached. Purely informational — never advice.
"""

import httpx

from app.core.config import get_settings
from app.db.supabase import get_supabase


def _user_email(user_id: str) -> str | None:
    try:
        res = get_supabase().auth.admin.get_user_by_id(user_id)
        return getattr(res.user, "email", None)
    except Exception:
        return None


def _send_email(to: str, subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.resend_api_key:
        return
    try:
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.resend_from,
                "to": [to],
                "subject": subject,
                "text": body,
            },
            timeout=10,
        )
    except Exception:
        pass


def notify(user_id: str, type_: str, title: str, body: str | None = None, email: bool = True) -> None:
    """Create an in-app notification; also email if a provider is configured."""
    try:
        get_supabase().table("notifications").insert({
            "user_id": user_id,
            "type": type_,
            "title": title,
            "body": body,
        }).execute()
    except Exception:
        pass

    if email:
        addr = _user_email(user_id)
        if addr:
            _send_email(addr, title, body or title)


def check_goals_reached(user_id: str) -> None:
    """Notify once when a goal's current value first reaches its target."""
    from app.api.routes.portfolio import compute_positions

    sb = get_supabase()
    goals = (
        sb.table("goals")
        .select("*")
        .eq("user_id", user_id)
        .eq("notified_reached", False)
        .execute()
    ).data or []
    if not goals:
        return

    try:
        positions = {p["base"]: p for p in compute_positions(user_id)["positions"]}
    except Exception:
        return

    for g in goals:
        p = positions.get(g["base"])
        if not p:
            continue
        current = p["current_value"] if p.get("current_value") is not None else p.get("invested", 0)
        target = g.get("target_amount") or 0
        if target and current >= target:
            name = g.get("title") or f"Objectif {g['base']}"
            notify(
                user_id,
                "goal_reached",
                f"🎉 Objectif atteint : {name}",
                f"Ta position en {g['base']} a atteint {round(current, 2)} {g['quote_currency']} "
                f"(objectif : {target} {g['quote_currency']}).",
            )
            sb.table("goals").update({"notified_reached": True}).eq("id", g["id"]).execute()
