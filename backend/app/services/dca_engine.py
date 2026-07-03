"""DCA execution engine.

For each due strategy: place the market buy(s) on the user's exchange, record
the trade(s), and schedule the next run. Failures are recorded as trades with
status=failed so the user sees them in history — the strategy is not silently
broken.

Two shapes of strategy:
  - single asset: `symbol` (e.g. BTC/EUR), the full amount buys it.
  - basket: `allocations` (e.g. 60% BTC, 40% ETH), the amount is split by
    weight and one buy per asset is placed. Each leg is recorded as its own
    trade, so the portfolio aggregation (by symbol) works unchanged.

Timing is precise: strategies carry run_hour/run_minute plus an optional
weekday (weekly/biweekly) or day-of-month (monthly). Schedules are computed in
Europe/Paris so the wall-clock time the user picked is respected.
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.db.supabase import get_supabase
from app.models.schemas import Interval
from app.services import exchange_service

MAX_CONSECUTIVE_FAILURES = 3
TZ = ZoneInfo("Europe/Paris")


def _set_time(dt: datetime, hour: int, minute: int) -> datetime:
    return dt.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _next_month(dt: datetime) -> datetime:
    year, month = (dt.year + 1, 1) if dt.month == 12 else (dt.year, dt.month + 1)
    return dt.replace(year=year, month=month, day=min(dt.day, 28))


def compute_first_run(
    interval: Interval,
    hour: int = 9,
    minute: int = 0,
    weekday: int | None = None,
    day_of_month: int | None = None,
    now: datetime | None = None,
) -> datetime:
    """First scheduled run strictly in the future, honoring the timing prefs."""
    now = (now or datetime.now(timezone.utc)).astimezone(TZ)
    interval = Interval(interval)

    if interval == Interval.daily:
        cand = _set_time(now, hour, minute)
        if cand <= now:
            cand += timedelta(days=1)
    elif interval in (Interval.weekly, Interval.biweekly):
        wd = weekday if weekday is not None else now.weekday()
        days_ahead = (wd - now.weekday()) % 7
        cand = _set_time(now + timedelta(days=days_ahead), hour, minute)
        if cand <= now:
            cand += timedelta(days=7)
    else:
        dom = day_of_month if day_of_month is not None else min(now.day, 28)
        cand = _set_time(now.replace(day=dom), hour, minute)
        if cand <= now:
            cand = _set_time(_next_month(cand), hour, minute)

    return cand.astimezone(timezone.utc)


def advance_run(
    interval: Interval,
    prev: datetime,
    hour: int = 9,
    minute: int = 0,
    day_of_month: int | None = None,
) -> datetime:
    """Next run after a previous scheduled slot (keeps weekday / day-of-month)."""
    p = prev.astimezone(TZ)
    interval = Interval(interval)

    if interval == Interval.daily:
        nxt = _set_time(p + timedelta(days=1), hour, minute)
    elif interval == Interval.weekly:
        nxt = _set_time(p + timedelta(days=7), hour, minute)
    elif interval == Interval.biweekly:
        nxt = _set_time(p + timedelta(days=14), hour, minute)
    else:
        nxt = _set_time(_next_month(p), hour, minute)
        if day_of_month is not None:
            nxt = nxt.replace(day=min(day_of_month, 28))

    return nxt.astimezone(timezone.utc)


def next_run_after(interval: Interval, base: datetime | None = None) -> datetime:
    """Backward-compatible helper (default 9:00 timing)."""
    return compute_first_run(interval, now=base)


def _legs(strategy: dict) -> list[tuple[str, float]]:
    quote = strategy["quote_currency"]
    amount = float(strategy["amount"])
    allocations = strategy.get("allocations")
    if allocations:
        return [
            (f"{a['base']}/{quote}", round(amount * float(a["weight"]) / 100.0, 2))
            for a in allocations
        ]
    return [(strategy["symbol"], amount)]


def execute_strategy(strategy: dict) -> dict:
    """Run one DCA cycle for a strategy row. Places one buy per leg."""
    sb = get_supabase()

    conn = (
        sb.table("exchange_connections")
        .select("*")
        .eq("id", strategy["exchange_connection_id"])
        .single()
        .execute()
    ).data

    any_success = False
    last_error: str | None = None
    executed: list[tuple[str, float]] = []

    try:
        client = exchange_service.client_from_connection(conn)
    except Exception as exc:
        client = None
        last_error = str(exc)

    quote = strategy["quote_currency"]
    for symbol, amount in _legs(strategy):
        trade = {
            "strategy_id": strategy["id"],
            "user_id": strategy["user_id"],
            "symbol": symbol,
            "amount": amount,
            "quote_currency": quote,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        if client is None:
            trade.update(status="failed", error=last_error)
        else:
            try:
                order = exchange_service.place_market_buy(client, symbol, amount)
                trade.update(
                    status="success",
                    price=order.get("average") or order.get("price"),
                    filled=order.get("filled"),
                )
                any_success = True
                executed.append((symbol.split("/")[0], amount))
            except Exception as exc:
                last_error = str(exc)
                trade.update(status="failed", error=last_error)
        sb.table("trades").insert(trade).execute()

    prev = strategy.get("next_run_at")
    prev_dt = datetime.fromisoformat(prev) if prev else datetime.now(timezone.utc)
    nxt = advance_run(
        strategy["interval"],
        prev_dt,
        strategy.get("run_hour", 9),
        strategy.get("run_minute", 0),
        strategy.get("run_day_of_month"),
    )
    now = datetime.now(timezone.utc)
    guard = 0
    while nxt <= now and guard < 120:
        nxt = advance_run(
            strategy["interval"], nxt,
            strategy.get("run_hour", 9),
            strategy.get("run_minute", 0),
            strategy.get("run_day_of_month"),
        )
        guard += 1

    updates: dict = {"next_run_at": nxt.isoformat()}

    if not any_success:
        failures = (strategy.get("consecutive_failures") or 0) + 1
        updates["consecutive_failures"] = failures
        updates["last_error"] = last_error
        if failures >= MAX_CONSECUTIVE_FAILURES:
            updates["status"] = "error"
    else:
        updates["consecutive_failures"] = 0
        updates["last_error"] = None

    sb.table("strategies").update(updates).eq("id", strategy["id"]).execute()

    _notify_run(strategy, executed, any_success, last_error, updates.get("status") == "error")
    return updates


def _notify_run(strategy, executed, any_success, last_error, suspended):
    from app.services import notifications

    user_id = strategy["user_id"]
    quote = strategy["quote_currency"]
    if any_success:
        detail = ", ".join(f"{amount} {quote} de {base}" for base, amount in executed)
        notifications.notify(user_id, "buy_executed", "Achat exécuté", f"Cadence a acheté {detail}.")
        notifications.check_goals_reached(user_id)
    elif suspended:
        notifications.notify(
            user_id, "plan_suspended", "Plan suspendu",
            f"Un plan a été suspendu après plusieurs échecs. Dernière erreur : {last_error}. "
            "Vérifie ton solde et ta clé API, puis réactive-le.",
        )
    else:
        notifications.notify(
            user_id, "buy_failed", "Achat échoué",
            f"Un achat n'a pas pu être exécuté. Erreur : {last_error}.",
        )


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
