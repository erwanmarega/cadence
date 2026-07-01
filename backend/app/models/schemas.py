from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


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


class Allocation(BaseModel):
    base: str = Field(min_length=1)
    weight: float = Field(gt=0, le=100)

    @field_validator("base")
    @classmethod
    def upper_base(cls, v: str) -> str:
        return v.upper()


class TimingFields(BaseModel):
    run_hour: int = Field(default=9, ge=0, le=23)
    run_minute: int = Field(default=0, ge=0, le=59)
    run_weekday: Optional[int] = Field(default=None, ge=0, le=6)
    run_day_of_month: Optional[int] = Field(default=None, ge=1, le=28)


class StrategyCreate(TimingFields):
    exchange_connection_id: str

    symbol: Optional[str] = Field(default=None, min_length=3)
    allocations: Optional[list[Allocation]] = None

    amount: float = Field(gt=0)
    quote_currency: str = Field(default="EUR", min_length=3, max_length=5)
    interval: Interval

    @field_validator("symbol")
    @classmethod
    def upper_symbol(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v

    @model_validator(mode="after")
    def check_target(self):
        if self.allocations:
            if self.symbol:
                raise ValueError("Renseigner soit une crypto, soit un panier — pas les deux.")
            total = round(sum(a.weight for a in self.allocations), 2)
            if total != 100:
                raise ValueError(f"La somme des poids doit faire 100 (actuellement {total}).")
        elif not self.symbol:
            raise ValueError("Renseigner une crypto ou un panier.")
        return self


class StrategyUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    interval: Optional[Interval] = None
    status: Optional[StrategyStatus] = None
    run_hour: Optional[int] = Field(default=None, ge=0, le=23)
    run_minute: Optional[int] = Field(default=None, ge=0, le=59)
    run_weekday: Optional[int] = Field(default=None, ge=0, le=6)
    run_day_of_month: Optional[int] = Field(default=None, ge=1, le=28)


class StrategyOut(BaseModel):
    id: str
    exchange_connection_id: str
    symbol: Optional[str] = None
    allocations: Optional[list[Allocation]] = None
    amount: float
    quote_currency: str
    interval: Interval
    status: StrategyStatus
    next_run_at: Optional[datetime] = None
    run_hour: int = 9
    run_minute: int = 0
    run_weekday: Optional[int] = None
    run_day_of_month: Optional[int] = None
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
