from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Exchange(str, Enum):
    kraken = "kraken"
    coinbase = "coinbase"


class Interval(str, Enum):
    daily = "daily"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"


class StrategyStatus(str, Enum):
    active = "active"
    paused = "paused"

    error = "error"


class TradeStatus(str, Enum):
    success = "success"
    failed = "failed"


class ExchangeConnectionCreate(BaseModel):
    exchange: Exchange
    api_key: str = Field(min_length=1)
    api_secret: str = Field(min_length=1)

    passphrase: Optional[str] = None


class ExchangeConnectionOut(BaseModel):
    id: str
    exchange: Exchange

    api_key_hint: str
    created_at: datetime


class StrategyCreate(BaseModel):
    exchange_connection_id: str

    symbol: str = Field(min_length=3)

    amount: float = Field(gt=0)
    quote_currency: str = Field(default="EUR", min_length=3, max_length=5)
    interval: Interval

    @field_validator("symbol")
    @classmethod
    def upper_symbol(cls, v: str) -> str:
        return v.upper()


class StrategyUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    interval: Optional[Interval] = None
    status: Optional[StrategyStatus] = None


class StrategyOut(BaseModel):
    id: str
    exchange_connection_id: str
    symbol: str
    amount: float
    quote_currency: str
    interval: Interval
    status: StrategyStatus
    next_run_at: Optional[datetime] = None
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    created_at: datetime


class TradeOut(BaseModel):
    id: str
    strategy_id: str
    symbol: str
    amount: float
    quote_currency: str
    price: Optional[float] = None
    filled: Optional[float] = None
    status: TradeStatus
    error: Optional[str] = None
    executed_at: datetime
