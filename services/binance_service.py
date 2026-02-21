import requests
from typing import List, Dict


class Binance:
    """Fetches OHLCV kline data from the Binance public API (no key required)."""

    BASE_URL = "https://api.binance.com/api/v3"

    # Maps readable timeframe strings to Binance interval codes
    INTERVAL_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1w": "1w",
    }

    @staticmethod
    def get_klines(symbol: str, interval: str, limit: int = 100) -> List[Dict]:
        """
        Fetch kline/candlestick data from Binance.

        Args:
            symbol: Trading pair (e.g. "BTCUSDT").
            interval: Candle interval (e.g. "1h", "4h", "1d").
            limit: Number of candles to fetch (max 1000).

        Returns:
            List of dicts with keys: open_time, open, high, low, close, volume.
        """
        binance_interval = Binance.INTERVAL_MAP.get(interval, interval)

        response = requests.get(
            f"{Binance.BASE_URL}/klines",
            params={
                "symbol": symbol.upper(),
                "interval": binance_interval,
                "limit": min(limit, 1000),
            },
            timeout=10,
        )
        response.raise_for_status()
        raw = response.json()

        return [
            {
                "open_time": candle[0],
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
            }
            for candle in raw
        ]
