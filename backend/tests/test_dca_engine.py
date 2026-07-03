"""Unit tests for pure DCA logic — no network, no Supabase, no secrets."""

from datetime import datetime, timezone

from app.models.schemas import Interval
from app.services import dca_engine, exchange_service

NOW = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)  # Wednesday


def test_first_run_weekly_aligns_to_weekday():
    run = dca_engine.compute_first_run(Interval.weekly, hour=9, minute=0, weekday=0, now=NOW)
    assert run > NOW
    assert run.astimezone(dca_engine.TZ).weekday() == 0  # Monday


def test_advance_weekly_keeps_weekday_and_adds_7_days():
    first = dca_engine.compute_first_run(Interval.weekly, hour=9, minute=0, weekday=0, now=NOW)
    nxt = dca_engine.advance_run(Interval.weekly, first, 9, 0)
    assert (nxt - first).days == 7
    assert nxt.astimezone(dca_engine.TZ).weekday() == 0


def test_first_run_monthly_uses_day_of_month():
    run = dca_engine.compute_first_run(Interval.monthly, hour=8, minute=30, day_of_month=15, now=NOW)
    local = run.astimezone(dca_engine.TZ)
    assert local.day == 15
    assert (local.hour, local.minute) == (8, 30)


def test_legs_single():
    s = {"quote_currency": "EUR", "amount": 20, "symbol": "BTC/EUR"}
    assert dca_engine._legs(s) == [("BTC/EUR", 20)]


def test_legs_basket_splits_by_weight():
    s = {
        "quote_currency": "EUR",
        "amount": 20,
        "allocations": [{"base": "BTC", "weight": 60}, {"base": "ETH", "weight": 40}],
    }
    assert dca_engine._legs(s) == [("BTC/EUR", 12.0), ("ETH/EUR", 8.0)]


class _StubOHLCV:
    def __init__(self, closes):
        self._closes = closes

    def fetch_ohlcv(self, symbol, timeframe, limit):
        return [[0, 0, 0, 0, c] for c in self._closes]


def test_dip_boost_disabled_returns_base():
    assert dca_engine.dip_amount(_StubOHLCV([100] * 31), "BTC/EUR", 20, {"dip_enabled": False}) == 20


def test_dip_boost_triggers_when_below_average():
    # 30 closes at 100 (MA=100), current 80 -> 80 <= 100*(1-0.1)=90 -> boost x2
    client = _StubOHLCV([100] * 30 + [80])
    s = {"dip_enabled": True, "dip_pct": 10, "dip_window": 30, "dip_multiplier": 2}
    assert dca_engine.dip_amount(client, "BTC/EUR", 20, s) == 40.0


def test_dip_boost_skips_when_not_low_enough():
    client = _StubOHLCV([100] * 30 + [95])  # 95 > 90 threshold
    s = {"dip_enabled": True, "dip_pct": 10, "dip_window": 30, "dip_multiplier": 2}
    assert dca_engine.dip_amount(client, "BTC/EUR", 20, s) == 20


class _StubLedger:
    def fetch_ledger(self, limit=100):
        return [
            {"type": "receive", "currency": "XRP", "amount": 5.28, "referenceId": "R1", "datetime": "2026-07-01T14:05:36Z"},
            {"type": "spend", "currency": "EUR", "amount": -4.95, "referenceId": "R1", "datetime": "2026-07-01T14:05:36Z"},
            {"type": "deposit", "currency": "EUR", "amount": 5.0, "referenceId": "R0", "datetime": "2026-07-01T14:05:02Z"},
        ]


def test_ledger_trades_reconstructs_instant_buy():
    rows = exchange_service.fetch_ledger_trades(_StubLedger())
    assert len(rows) == 1
    r = rows[0]
    assert r["symbol"] == "XRP/EUR"
    assert r["side"] == "buy"
    assert r["amount"] == 4.95
    assert r["filled"] == 5.28
    assert round(r["price"], 4) == round(4.95 / 5.28, 4)
