"""Market trends — FACTUAL, INFORMATIONAL ONLY.

Per CLAUDE.md (assistant éducatif): we may show neutral price movement
("le Bitcoin a baissé de 5% sur 24h"). We must NEVER recommend buying,
selling, timing, or an amount — that is regulated investment advice
(AMF/CIF in France) and is out of scope. No endpoint here returns a
recommendation; only observed prices and 24h variation.
"""

from datetime import datetime, timezone

import ccxt
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/market", tags=["market"])


WATCHLIST = [
    "BTC/EUR", "ETH/EUR", "SOL/EUR", "XRP/EUR", "ADA/EUR", "DOT/EUR",
    "DOGE/EUR", "LTC/EUR", "LINK/EUR", "AVAX/EUR", "ATOM/EUR", "XLM/EUR",
]

_client: ccxt.Exchange | None = None


def _kraken() -> ccxt.Exchange:
    global _client
    if _client is None:
        _client = ccxt.kraken({"enableRateLimit": True})
    return _client


@router.get("/trends")
def trends():
    """Neutral 24h price movement for a watchlist of major coins."""
    try:
        tickers = _kraken().fetch_tickers(WATCHLIST)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Données marché indisponibles: {exc}")

    coins = []
    for symbol, t in tickers.items():
        last = t.get("last")
        pct = t.get("percentage")
        if last is None or pct is None:
            continue
        coins.append({
            "symbol": symbol,
            "base": symbol.split("/")[0],
            "last": last,
            "change_24h": round(pct, 2),
        })

    coins.sort(key=lambda c: c["change_24h"], reverse=True)
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "coins": coins,
    }
