"""In-app notifications: list recent + unread count, mark as read."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_user_id
from app.db.supabase import get_supabase

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: str
    type: str
    title: str
    body: Optional[str] = None
    read: bool
    created_at: datetime


@router.get("")
def list_notifications(user_id: str = Depends(get_current_user_id)):
    items = (
        get_supabase()
        .table("notifications")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    ).data or []
    unread = sum(1 for n in items if not n["read"])
    return {"items": items, "unread": unread}


class MarkReadBody(BaseModel):
    ids: Optional[list[str]] = None


@router.post("/read")
def mark_read(body: MarkReadBody, user_id: str = Depends(get_current_user_id)):
    query = get_supabase().table("notifications").update({"read": True}).eq("user_id", user_id)
    if body.ids:
        query = query.in_("id", body.ids)
    else:
        query = query.eq("read", False)
    query.execute()
    return {"ok": True}
