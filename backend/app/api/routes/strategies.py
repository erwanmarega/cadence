"""DCA strategy routes: create, list, update (incl. pause), delete.

Pause/resume = the emergency stop required by CLAUDE.md. A paused strategy
is skipped by the scheduler.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user_id
from app.db.supabase import get_supabase
from app.models.schemas import (
    StrategyCreate,
    StrategyOut,
    StrategyStatus,
    StrategyUpdate,
)
from app.services.dca_engine import compute_first_run

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.post("", response_model=StrategyOut, status_code=201)
def create_strategy(
    body: StrategyCreate,
    user_id: str = Depends(get_current_user_id),
):
    sb = get_supabase()

    conn = (
        sb.table("exchange_connections")
        .select("id")
        .eq("id", body.exchange_connection_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not conn.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange connection not found",
        )

    first_run = compute_first_run(
        body.interval,
        hour=body.run_hour,
        minute=body.run_minute,
        weekday=body.run_weekday,
        day_of_month=body.run_day_of_month,
    )

    row = {
        "user_id": user_id,
        "exchange_connection_id": body.exchange_connection_id,
        "symbol": body.symbol,
        "allocations": [a.model_dump() for a in body.allocations] if body.allocations else None,
        "amount": body.amount,
        "quote_currency": body.quote_currency.upper(),
        "interval": body.interval.value,
        "status": StrategyStatus.active.value,
        "run_hour": body.run_hour,
        "run_minute": body.run_minute,
        "run_weekday": body.run_weekday,
        "run_day_of_month": body.run_day_of_month,
        "next_run_at": first_run.isoformat(),
    }
    resp = sb.table("strategies").insert(row).execute()
    return resp.data[0]


@router.get("", response_model=list[StrategyOut])
def list_strategies(user_id: str = Depends(get_current_user_id)):
    resp = (
        get_supabase()
        .table("strategies")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data


@router.patch("/{strategy_id}", response_model=StrategyOut)
def update_strategy(
    strategy_id: str,
    body: StrategyUpdate,
    user_id: str = Depends(get_current_user_id),
):
    sb = get_supabase()
    updates = body.model_dump(exclude_none=True)

    for k, v in list(updates.items()):
        if hasattr(v, "value"):
            updates[k] = v.value
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if updates.get("status") == "active":
        updates["consecutive_failures"] = 0
        updates["last_error"] = None

    timing_keys = {"interval", "run_hour", "run_minute", "run_weekday", "run_day_of_month"}
    if timing_keys & updates.keys():
        current = (
            sb.table("strategies").select("*").eq("id", strategy_id).eq("user_id", user_id).execute()
        ).data
        if not current:
            raise HTTPException(status_code=404, detail="Strategy not found")
        merged = {**current[0], **updates}
        updates["next_run_at"] = compute_first_run(
            merged["interval"],
            hour=merged.get("run_hour") or 9,
            minute=merged.get("run_minute") or 0,
            weekday=merged.get("run_weekday"),
            day_of_month=merged.get("run_day_of_month"),
        ).isoformat()

    resp = (
        sb.table("strategies")
        .update(updates)
        .eq("id", strategy_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return resp.data[0]


@router.delete("/{strategy_id}", status_code=204)
def delete_strategy(strategy_id: str, user_id: str = Depends(get_current_user_id)):
    (
        get_supabase()
        .table("strategies")
        .delete()
        .eq("id", strategy_id)
        .eq("user_id", user_id)
        .execute()
    )
