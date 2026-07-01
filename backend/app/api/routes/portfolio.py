"""Portfolio performance: invested vs current value, average buy price, and
value history over time.

Aggregates the user's SUCCESSFUL trades per asset:
  - invested   = sum of fiat spent
  - quantity   = sum of crypto filled
  - avg_price  = invested / quantity  (the DCA average — the key metric)
  - current_value = quantity * live price (public ccxt)
  - P/L        = current_value - invested

Read-only and per-user (filtered by user_id). Live prices are public market
data; no exchange key is used here.
"""

from datetime import datetime, timezone

import ccxt
from fastapi import APIRouter, Depends

from app.core.deps import get_current_user_id
from app.db.supabase import get_supabase

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

_client: ccxt.Exchange | None = None


def _kraken() -> ccxt.Exchange:
    global _client
    if _client is None:
        _client = ccxt.kraken({"enableRateLimit": True})
    return _client


def _success_trades(user_id: str) -> list[dict]:
    sb = get_supabase()
    return (
        sb.table("trades")
        .select("symbol, amount, filled, quote_currency, status, executed_at")
        .eq("user_id", user_id)
        .eq("status", "success")
        .order("executed_at")
        .execute()
    ).data or []


def compute_positions(user_id: str) -> dict:
    """Aggregate positions + live valuation. Reused by goals."""
    trades = _success_trades(user_id)

    agg: dict[str, dict] = {}
    for t in trades:
        if not t.get("filled"):
            continue
        a = agg.setdefault(t["symbol"], {
            "symbol": t["symbol"],
            "base": t["symbol"].split("/")[0],
            "quote_currency": t["quote_currency"],
            "invested": 0.0,
            "quantity": 0.0,
        })
        a["invested"] += float(t["amount"])
        a["quantity"] += float(t["filled"])

    positions = list(agg.values())

    prices: dict[str, float] = {}
    if positions:
        try:
            tickers = _kraken().fetch_tickers([p["symbol"] for p in positions])
            prices = {s: t.get("last") for s, t in tickers.items()}
        except Exception:
            prices = {}

    invested_total = 0.0
    value_total = 0.0
    quote = positions[0]["quote_currency"] if positions else "EUR"

    for p in positions:
        p["avg_price"] = round(p["invested"] / p["quantity"], 2) if p["quantity"] else None
        price = prices.get(p["symbol"])
        p["current_price"] = round(price, 2) if price else None
        if price:
            cv = p["quantity"] * price
            p["current_value"] = round(cv, 2)
            p["pl"] = round(cv - p["invested"], 2)
            p["pl_pct"] = round((cv - p["invested"]) / p["invested"] * 100, 2) if p["invested"] else None
            value_total += cv
        else:
            p["current_value"] = None
            p["pl"] = None
            p["pl_pct"] = None
        p["invested"] = round(p["invested"], 2)
        invested_total += p["invested"]

    pl_total = round(value_total - invested_total, 2) if value_total else None
    pl_pct_total = (
        round((value_total - invested_total) / invested_total * 100, 2)
        if value_total and invested_total else None
    )

    return {
        "quote_currency": quote,
        "invested_total": round(invested_total, 2),
        "current_value_total": round(value_total, 2) if value_total else None,
        "pl_total": pl_total,
        "pl_pct_total": pl_pct_total,
        "positions": sorted(positions, key=lambda p: p["invested"], reverse=True),
    }


@router.get("/summary")
def summary(user_id: str = Depends(get_current_user_id)):
    return compute_positions(user_id)


@router.get("/history")
def history(user_id: str = Depends(get_current_user_id)):
    """Daily time series: cumulative invested vs estimated portfolio value.

    Value uses historical daily closes (public OHLCV). Best-effort: if a
    symbol's history can't be fetched, that symbol contributes only to
    invested (value falls back to invested for those days).
    """
    trades = _success_trades(user_id)
    if not trades:
        return {"quote_currency": "EUR", "points": []}

    quote = trades[0]["quote_currency"]
    symbols = sorted({t["symbol"] for t in trades if t.get("filled")})


    first = datetime.fromisoformat(trades[0]["executed_at"]).date()
    today = datetime.now(timezone.utc).date()
    days = (today - first).days + 1
    if days < 1:
        days = 1


    closes: dict[str, dict] = {}
    client = _kraken()
    for sym in symbols:
        try:
            since = client.parse8601(f"{first.isoformat()}T00:00:00Z")
            ohlcv = client.fetch_ohlcv(sym, "1d", since=since, limit=days + 2)
            m = {}
            for row in ohlcv:
                d = datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc).date().isoformat()
                m[d] = row[4]
            closes[sym] = m
        except Exception:
            closes[sym] = {}


    from datetime import timedelta

    points = []
    last_price: dict[str, float] = {}
    for i in range(days):
        day = first + timedelta(days=i)
        day_iso = day.isoformat()

        invested = 0.0
        qty: dict[str, float] = {}
        for t in trades:
            if not t.get("filled"):
                continue
            tdate = datetime.fromisoformat(t["executed_at"]).date()
            if tdate <= day:
                invested += float(t["amount"])
                qty[t["symbol"]] = qty.get(t["symbol"], 0.0) + float(t["filled"])

        value = 0.0
        valued = True
        for sym, q in qty.items():
            price = closes.get(sym, {}).get(day_iso) or last_price.get(sym)
            if price:
                last_price[sym] = price
                value += q * price
            else:
                valued = False
        points.append({
            "date": day_iso,
            "invested": round(invested, 2),
            "value": round(value, 2) if valued and value else None,
        })

    return {"quote_currency": quote, "points": points}
