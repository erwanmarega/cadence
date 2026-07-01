"""DCA execution engine.

For each due strategy: place a market buy on the user's exchange, record
the trade, and schedule the next run. Failures are recorded as trades with
status=failed so the user sees them in history — the strategy is not
silently broken.
"""

from datetime import datetime, timedelta, timezone

from app.db.supabase import get_supabase
from app.models.schemas import Interval
from app.services import exchange_service

_INTERVAL_DELTA = {
    Interval.daily: timedelta(days=1),
    Interval.weekly: timedelta(weeks=1),
    Interval.biweekly: timedelta(weeks=2),
    Interval.monthly: timedelta(days=30),
}


MAX_CONSECUTIVE_FAILURES = 3


def next_run_after(interval: Interval, base: datetime | None = None) -> datetime:
    base = base or datetime.now(timezone.utc)
    return base + _INTERVAL_DELTA[Interval(interval)]


def execute_strategy(strategy: dict) -> dict:
    """Run one DCA buy for a strategy row. Returns the trade row written."""
    sb = get_supabase()

    conn_resp = (
        sb.table("exchange_connections")
        .select("*")
        .eq("id", strategy["exchange_connection_id"])
        .single()
        .execute()
    )
    conn = conn_resp.data

    trade: dict = {
        "strategy_id": strategy["id"],
        "user_id": strategy["user_id"],
        "symbol": strategy["symbol"],
        "amount": strategy["amount"],
        "quote_currency": strategy["quote_currency"],
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }

    failed = False
    try:
        client = exchange_service.client_from_connection(conn)
        order = exchange_service.place_market_buy(
            client, strategy["symbol"], strategy["amount"]
        )
        trade.update(
            status="success",
            price=order.get("average") or order.get("price"),
            filled=order.get("filled"),
        )
    except Exception as exc:
        failed = True
        error_msg = str(exc)
        trade.update(status="failed", error=error_msg)

    sb.table("trades").insert(trade).execute()


    updates: dict = {"next_run_at": next_run_after(strategy["interval"]).isoformat()}

    if failed:
        failures = (strategy.get("consecutive_failures") or 0) + 1
        updates["consecutive_failures"] = failures
        updates["last_error"] = error_msg


        if failures >= MAX_CONSECUTIVE_FAILURES:
            updates["status"] = "error"
    else:

        updates["consecutive_failures"] = 0
        updates["last_error"] = None

    sb.table("strategies").update(updates).eq("id", strategy["id"]).execute()

    return trade


def run_due_strategies() -> int:
    """Execute all active strategies whose next_run_at has passed."""
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    resp = (
        sb.table("strategies")
        .select("*")
        .eq("status", "active")
        .lte("next_run_at", now)
        .execute()
    )
    due = resp.data or []
    for strategy in due:
        execute_strategy(strategy)
    return len(due)
