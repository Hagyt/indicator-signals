from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SMTDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass
class SwingPoint:
    timestamp: float
    price: float
    bar_index: int
    swing_type: str  # "high" or "low"


@dataclass
class SMTDivergence:
    direction: SMTDirection
    timestamp: float
    asset_a_symbol: str
    asset_b_symbol: str
    asset_a_prev_price: float
    asset_a_curr_price: float
    asset_b_prev_price: float
    asset_b_curr_price: float
    swing_type: str  # "high" or "low"
    timeframe: str

    @property
    def description(self) -> str:
        if self.direction == SMTDirection.BEARISH:
            return (
                f"Bearish SMT: {self.asset_a_symbol} vs {self.asset_b_symbol} "
                f"diverged at swing highs on {self.timeframe}"
            )
        return (
            f"Bullish SMT: {self.asset_a_symbol} vs {self.asset_b_symbol} "
            f"diverged at swing lows on {self.timeframe}"
        )


@dataclass
class SMTPairConfig:
    asset_a: str  # e.g. "BTCUSDT"
    asset_b: str  # e.g. "ETHUSDT"
    label_a: str  # e.g. "BTC"
    label_b: str  # e.g. "ETH"
    timeframes: list = field(default_factory=lambda: ["1h", "4h"])
    swing_left: int = 5
    swing_right: int = 2
    max_offset_bars: int = 3
