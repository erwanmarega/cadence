"""DCA backtest simulation — PUBLIC, no auth, no real money.

Replays a fixed-amount DCA over real historical prices: "if you had put
X€/interval in <coin> since <date>, what would it be worth now?".

Strictly informational (CLAUDE.md): shows a factual past scenario, never a
recommendation. Past performance is not indicative of future results — the
frontend states this, and lets the user pick losing periods too.
"""

from datetime import datetime, timedelta, timezone

import bisect

import ccxt
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/simulate", tags=["simulate"])

ALLOWED_BASES = ["BTC", "ETH", "SOL", "ADA", "DOT", "XRP", "LTC"]
_INTERVAL_DAYS = {"daily": 1, "weekly": 7, "biweekly": 14, "monthly": 30}

_client: ccxt.Exchange | None = None


def _kraken() -> ccxt.Exchange:
    global _client
    if _client is None:
        _client = ccxt.kraken({"enableRateLimit": True})
    return _client


def _price_history(symbol: str, since_ms: int) -> tuple[list[str], list[float]]:
    """Weekly closes from `since` to now, as parallel sorted lists.

    Weekly timeframe ('1w') is used because Kraken caps OHLCV at ~720 candles
    per timeframe: 720 weeks (~13 years) easily covers any start date, whereas
    720 daily candles only reach ~2 years back.
    """
    client = _kraken()
    rows = client.fetch_ohlcv(symbol, "1w", since=since_ms, limit=720)
    days, closes = [], []
    for row in rows:
        d = datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc).date().isoformat()
        days.append(d)
        closes.append(row[4])
    return days, closes


@router.get("")
def simulate(
    base: str = Query(...),
    amount: float = Query(..., gt=0),
    interval: str = Query("weekly"),
    start: str = Query(..., description="YYYY-MM-DD"),
    quote: str = Query("EUR"),
):
    base = base.upper()
    if base not in ALLOWED_BASES:
        raise HTTPException(400, f"Crypto non supportée. Choix: {', '.join(ALLOWED_BASES)}")
    if interval not in _INTERVAL_DAYS:
        raise HTTPException(400, "Intervalle invalide")
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "Date invalide (YYYY-MM-DD)")

    today = datetime.now(timezone.utc).date()
    if start_date >= today:
        raise HTTPException(400, "La date de début doit être dans le passé")

    symbol = f"{base}/{quote.upper()}"
    since_ms = _kraken().parse8601(f"{start_date.isoformat()}T00:00:00Z")
    days, closes = _price_history(symbol, since_ms)
    if not closes:
        raise HTTPException(502, "Historique de prix indisponible pour cette paire")

    last_price = closes[-1]

    def price_on(day_iso: str) -> float | None:

        i = bisect.bisect_right(days, day_iso) - 1
        return closes[i] if i >= 0 else None


    step = timedelta(days=_INTERVAL_DAYS[interval])
    buy_dates = []
    d = start_date
    while d <= today:
        buy_dates.append(d)
        d += step
    buy_set = {bd.isoformat(): None for bd in buy_dates}


    invested = 0.0
    qty = 0.0
    points = []
    cur = start_date
    while cur <= today:
        iso = cur.isoformat()
        if iso in buy_set:
            p = price_on(iso)
            if p:
                qty += amount / p
                invested += amount
        dp = price_on(iso)
        value = qty * dp if dp else None
        points.append({
            "date": iso,
            "invested": round(invested, 2),
            "value": round(value, 2) if value is not None else None,
        })
        cur += timedelta(days=1)

    current_value = round(qty * last_price, 2)
    avg_price = round(invested / qty, 2) if qty else None
    pl = round(current_value - invested, 2)
    pl_pct = round((current_value - invested) / invested * 100, 2) if invested else None


    if len(points) > 120:
        stepn = len(points) // 120 + 1
        sampled = points[::stepn]
        if sampled[-1]["date"] != points[-1]["date"]:
            sampled.append(points[-1])
        points = sampled

    return {
        "base": base,
        "quote_currency": quote.upper(),
        "amount": amount,
        "interval": interval,
        "start": start_date.isoformat(),
        "buys": len(buy_dates),
        "invested": round(invested, 2),
        "quantity": qty,
        "avg_price": avg_price,
        "current_value": current_value,
        "current_price": round(last_price, 2),
        "pl": pl,
        "pl_pct": pl_pct,
        "points": points,
    }
