"""Trade history routes (read-only)."""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_id
from app.db.supabase import get_supabase
from app.models.schemas import TradeOut

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=list[TradeOut])
def list_trades(
    user_id: str = Depends(get_current_user_id),
    strategy_id: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
):
    query = (
        get_supabase()
        .table("trades")
        .select("*")
        .eq("user_id", user_id)
    )
    if strategy_id:
        query = query.eq("strategy_id", strategy_id)
    resp = query.order("executed_at", desc=True).limit(limit).execute()
    return resp.data
