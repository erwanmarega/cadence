"""Exchange access via ccxt.

Hard rule (CLAUDE.md): the bot is non-custodial. It only ever places
market BUY orders. There is NO code path that withdraws funds. API keys
should be created by the user WITHOUT withdrawal permission; we also never
call any withdrawal endpoint.
"""

import ccxt

from app.core.security import decrypt
from app.models.schemas import Exchange

_EXCHANGE_CLASSES = {
    Exchange.kraken: ccxt.kraken,
    Exchange.coinbase: ccxt.coinbase,
}


def _build_client(exchange: Exchange, api_key: str, api_secret: str,
                  passphrase: str | None) -> ccxt.Exchange:
    klass = _EXCHANGE_CLASSES[exchange]
    config = {
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
    }
    if passphrase:
        config["password"] = passphrase
    return klass(config)


def client_from_connection(conn: dict) -> ccxt.Exchange:
    """Build a ccxt client from a stored (encrypted) connection row."""
    return _build_client(
        Exchange(conn["exchange"]),
        decrypt(conn["api_key_enc"]),
        decrypt(conn["api_secret_enc"]),
        decrypt(conn["passphrase_enc"]) if conn.get("passphrase_enc") else None,
    )


def verify_credentials(exchange: Exchange, api_key: str, api_secret: str,
                       passphrase: str | None) -> None:
    """Validate keys by a read-only balance fetch. Raises on failure."""
    client = _build_client(exchange, api_key, api_secret, passphrase)
    client.fetch_balance()


def fetch_recent_trades(client: ccxt.Exchange, limit: int = 100) -> list[dict]:
    """Read the account's recent trades from the exchange (read-only).

    Uses the query/read permission of the API key — never withdrawal. Returns
    a normalized list; each item mirrors a Cadence trade row's fields. Raises
    on API errors (e.g. missing read permission) so the caller can report them.
    """
    raw = client.fetch_my_trades(limit=limit)

    out = []
    for t in raw:
        symbol = t.get("symbol")
        if not symbol or "/" not in symbol:
            continue
        out.append({
            "ext_id": str(t.get("id")) if t.get("id") is not None else None,
            "symbol": symbol,
            "quote_currency": symbol.split("/")[1],
            "side": t.get("side"),
            "amount": t.get("cost"),
            "filled": t.get("amount"),
            "price": t.get("price"),
            "executed_at": t.get("datetime"),
        })
    return out


_FIAT = {"EUR", "USD", "GBP", "CHF", "CAD", "AUD", "JPY", "ZEUR", "ZUSD"}


def fetch_ledger_trades(client: ccxt.Exchange, limit: int = 100) -> list[dict]:
    """Reconstruct instant buys/sells from the account ledger (read-only).

    Kraken "instant buys" (simple interface) never appear as spot trades or
    orders — only as paired ledger entries (a `spend` of fiat + a `receive` of
    crypto sharing a referenceId). We group by referenceId to rebuild each
    acquisition. Requires the ledger read permission; never withdrawal.
    """
    entries = client.fetch_ledger(limit=limit)

    groups: dict[str, list[dict]] = {}
    for e in entries:
        if e.get("type") not in ("spend", "receive"):
            continue
        ref = e.get("referenceId") or e.get("id")
        if ref:
            groups.setdefault(ref, []).append(e)

    out = []
    for ref, es in groups.items():
        crypto = next((x for x in es if (x.get("currency") or "").upper() not in _FIAT), None)
        fiat = next((x for x in es if (x.get("currency") or "").upper() in _FIAT), None)
        if not crypto or not fiat:
            continue
        filled = abs(float(crypto.get("amount") or 0))
        spent = abs(float(fiat.get("amount") or 0))
        if not filled or not spent:
            continue
        out.append({
            "ext_id": ref,
            "symbol": f"{crypto['currency']}/{fiat['currency']}",
            "quote_currency": fiat["currency"],
            "side": "buy" if crypto.get("type") == "receive" else "sell",
            "amount": spent,
            "filled": filled,
            "price": spent / filled,
            "executed_at": crypto.get("datetime") or fiat.get("datetime"),
        })
    return out


def place_market_buy(client: ccxt.Exchange, symbol: str, quote_amount: float) -> dict:
    """Place a market BUY spending `quote_amount` of quote currency.

    Returns the ccxt order dict. Only buys — never sells, never withdraws.
    """
    client.load_markets()


    params = {"createMarketBuyOrderRequiresPrice": False}
    return client.create_order(symbol, "market", "buy", quote_amount, None, params)
