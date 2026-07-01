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


def place_market_buy(client: ccxt.Exchange, symbol: str, quote_amount: float) -> dict:
    """Place a market BUY spending `quote_amount` of quote currency.

    Returns the ccxt order dict. Only buys — never sells, never withdraws.
    """
    client.load_markets()


    params = {"createMarketBuyOrderRequiresPrice": False}
    return client.create_order(symbol, "market", "buy", quote_amount, None, params)
