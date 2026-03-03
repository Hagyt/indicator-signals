# Research 1.1 — Python Libraries for Fetching Market Data (OHLCV)

> **Task:** Research and select the best Python libraries for fetching market data (OHLCV) across crypto (and later forex/stocks). Compare `ccxt`, `python-binance`, and alternatives.

---

## Libraries Evaluated

### 1. CCXT (CryptoCurrency eXchange Trading Library)

**What it is:** A unified API for connecting to 107+ cryptocurrency exchanges. Write code once, it works across Binance, Bybit, Kraken, Coinbase, etc.

**GitHub:** ~41,100 stars | ~550 contributors | MIT License
**PyPI:** ~1.3 million monthly downloads | Latest release: Feb 23, 2026 (v4.5.40)
**Languages:** Python, JavaScript/TypeScript, PHP, C#, Go

**Strengths:**
- Exchange-agnostic: identical method signatures regardless of exchange (`exchange.fetch_ohlcv('BTC/USDT', '1d', limit=100)`)
- Covers both REST and WebSocket APIs (WebSocket via CCXT Pro)
- Extremely active development — releases multiple times per week
- Massive community and ecosystem (Freqtrade, OctoBot, and many trading bots built on it)
- Handles pagination, rate limiting, and exchange quirks automatically
- Supports both sync and async Python
- Concurrent OHLCV pagination for performance
- Also has a dedicated Binance-specific SDK for deeper integration

**Weaknesses:**
- Abstraction overhead — slightly slower than direct exchange APIs
- Crypto-only — does NOT natively support forex or traditional stocks
- Large package size due to 107+ exchange implementations
- ECDSA signing in pure Python can be slow (45ms) unless `coincurve` is installed (drops to <0.05ms)
- Optional 1 bps builder fee on some exchanges (can be disabled with `exchange.options['builderFee'] = False`)

**OHLCV API Example:**
```python
import ccxt

exchange = ccxt.binance()
ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1d', limit=100)
# Returns: [[timestamp, open, high, low, close, volume], ...]
```

---

### 2. python-binance

**What it is:** A dedicated Python wrapper for the Binance exchange API (spot, margin, futures, mining, Simple Earn).

**GitHub:** ~6,824 stars | Maintained by sammchardy
**PyPI:** Latest release: Feb 16, 2026 (v1.0.34) | Healthy maintenance status
**Languages:** Python only

**Strengths:**
- Deep Binance integration — access to every Binance-specific feature
- Recommended in Binance's own API documentation
- No abstraction overhead — direct API access means potentially lower latency
- Supports `orjson` for faster JSON parsing (auto-detected if installed)
- Generator-based historical klines for memory-efficient large data fetching
- Separate methods for spot vs. futures klines
- Active releases (8+ versions in the past year)

**Weaknesses:**
- Binance-only — no support for any other exchange
- 1,000-candle limit per API request (must paginate for larger ranges)
- Binance rate limits: 1,200 request weight per minute; each kline call uses 2 weight
- Frequent API breaking changes from Binance (wapi→sapi migration, WebSocket changes)
- No unified interface — if you later want Kraken or Bybit, you need a different library

**OHLCV API Example:**
```python
from binance.client import Client

client = Client(api_key, api_secret)
klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1DAY, "1 Jan 2024")
# Returns: [[open_time, open, high, low, close, volume, close_time, ...], ...]
```

---

### 3. yfinance (Yahoo Finance)

**What it is:** An unofficial Python client for Yahoo Finance data. Covers stocks, ETFs, forex, indices, and some crypto.

**PyPI:** v1.0 released Jan 24, 2026
**Languages:** Python only

**Strengths:**
- Free access to stocks, ETFs, forex, and crypto data
- Multi-asset class coverage (the only library here that covers traditional markets)
- Simple API: `yf.download('AAPL', start='2024-01-01')` returns a pandas DataFrame
- Batch downloads for multiple tickers
- Also provides fundamentals, earnings, dividends, splits

**Weaknesses:**
- UNOFFICIAL and UNRELIABLE — scrapes Yahoo Finance, no SLA, can break at any time
- Aggressive rate limiting in 2025-2026 — many users report `YFRateLimitError` even with modest usage
- Shared cloud IPs (e.g., Streamlit Cloud) are especially rate-limited
- Intraday data limited to last 60 days
- Not suitable for production trading systems
- Data can be incomplete or inconsistent

**OHLCV API Example:**
```python
import yfinance as yf

data = yf.download('BTC-USD', start='2024-01-01', end='2025-01-01')
# Returns: pandas DataFrame with Open, High, Low, Close, Volume columns
```

---

### 4. Cryptofeed

**What it is:** A Python library focused on real-time WebSocket data streaming from cryptocurrency exchanges.

**GitHub:** bmoscon/cryptofeed
**Languages:** Python only

**Strengths:**
- Purpose-built for low-latency, real-time WebSocket data
- Normalized data format across exchanges
- Supports backend callbacks (write directly to databases, Kafka, etc.)
- Synthetic NBBO (best bid/offer aggregated across exchanges)
- Complementary to CCXT — use cryptofeed for streaming, CCXT for REST

**Weaknesses:**
- WebSocket-focused — limited REST/historical data support
- Smaller community than CCXT
- More complex setup (callback-based architecture)
- Overkill for periodic OHLCV signal checking (more suited for HFT)

---

### 5. Other Notable Alternatives

| Library | Use Case | Notes |
|---------|----------|-------|
| **binance-connector-python** | Official Binance SDK | Auto-generated, less ergonomic than python-binance |
| **tardis-python** | Tick-level historical data | Great for HFT backtesting, overkill for candle-based signals |
| **Alpha Vantage** | Stocks, forex, crypto | Free tier: 25 calls/day — too limited for production |
| **tessa** | Simple price access | Wraps yfinance + pycoingecko; convenience layer |
| **Alpaca API** | US stocks + crypto | CCXT integration available; US-focused |

---

## Comparison Matrix

| Criteria | CCXT | python-binance | yfinance | Cryptofeed |
|----------|------|----------------|----------|------------|
| **Exchanges supported** | 107+ | 1 (Binance) | Yahoo Finance | ~20+ |
| **Asset classes** | Crypto only | Crypto only | Stocks, forex, crypto | Crypto only |
| **OHLCV REST** | Excellent | Excellent | Good (unreliable) | Limited |
| **WebSocket** | Yes (Pro) | Yes | No | Excellent |
| **Maintenance** | Very active | Active | Active | Active |
| **Community size** | Very large (41k stars) | Large (6.8k stars) | Large | Medium |
| **Ease of use** | Easy | Easy | Very easy | Moderate |
| **Production-ready** | Yes | Yes | No | Yes |
| **Future forex/stock support** | No (crypto only) | No | Yes | No |
| **Rate limit handling** | Built-in | Manual | Fragile | Built-in |
| **Free / open source** | MIT | MIT | Apache 2.0 | License varies |

---

## Recommendation

### Primary choice: **CCXT**

**Rationale:**
1. **Multi-exchange support** is critical. The app's task plan calls for configurable asset pairs and data sources. Being locked to Binance is too restrictive — exchanges go down, get delisted in regions, or change APIs. CCXT makes switching exchanges a config change.
2. **Unified OHLCV interface** — `fetch_ohlcv()` works identically across all 107+ exchanges with automatic pagination and rate limit handling.
3. **Ecosystem maturity** — 41k GitHub stars, 1.3M monthly downloads, 550+ contributors. Battle-tested in production by Freqtrade, OctoBot, and thousands of trading bots.
4. **Active development** — multiple releases per week, immediate support for new exchange API changes.
5. **Async support** — important for fetching data from multiple pairs/timeframes concurrently.

### For future forex/stocks expansion: **yfinance** (research/prototyping) or **a paid API** (production)

CCXT is crypto-only, so for the future forex/stocks goal mentioned in the task plan, we'll need a separate data provider. The architecture should define an abstract market data interface (port) so the provider can be swapped. Options:
- **yfinance** — acceptable for prototyping and personal use, but too unreliable for production
- **Alpaca** — good for US stocks + crypto, has CCXT integration
- **Alpha Vantage / Polygon.io / Tiingo** — paid APIs with better reliability

### Not recommended as primary: **python-binance**

While python-binance is well-maintained and performant, its single-exchange limitation conflicts with the app's design goal of a pluggable, exchange-agnostic architecture. However, if Binance-specific features are ever needed beyond what CCXT provides, the CCXT team now offers a dedicated `ccxt/binance-python` SDK that combines CCXT's unified interface with Binance-specific depth.

---

## Sources

- [CCXT GitHub Repository](https://github.com/ccxt/ccxt)
- [CCXT Documentation](https://docs.ccxt.com/)
- [CCXT on PyPI](https://pypi.org/project/ccxt/)
- [CCXT Package Health Analysis (Snyk)](https://snyk.io/advisor/python/ccxt)
- [python-binance GitHub Repository](https://github.com/sammchardy/python-binance)
- [python-binance Documentation](https://python-binance.readthedocs.io/)
- [python-binance on PyPI](https://pypi.org/project/python-binance/)
- [python-binance Package Health Analysis (Snyk)](https://snyk.io/advisor/python/python-binance)
- [yfinance on PyPI](https://pypi.org/project/yfinance/)
- [yfinance Guide — AlgoTrading101](https://algotrading101.com/learn/yfinance-guide/)
- [yfinance Practical Guide — TheLinuxCode](https://thelinuxcode.com/what-the-yfinance-library-is-and-isnt-a-practical-guide-to-yahoo-finance-data-in-python/)
- [Cryptofeed GitHub Repository](https://github.com/bmoscon/cryptofeed)
- [Comparing CCXT with Other Crypto Trading Libraries — Sling Academy](https://www.slingacademy.com/article/comparing-ccxt-with-other-crypto-trading-libraries-in-python/)
- [Top Crypto Libraries for Python Developers in 2025 — Analytics Insight](https://www.analyticsinsight.net/programming/top-crypto-libraries-for-python-developers-in-2025)
- [Ultimate Python Quantitative Trading Ecosystem Guide — Medium](https://medium.com/@mahmoud.abdou2002/the-ultimate-python-quantitative-trading-ecosystem-2025-guide-074c480bce2e)
- [Binance Python API Guide — AlgoTrading101](https://algotrading101.com/learn/binance-python-api-guide/)
- [CCXT + Alpaca Integration](https://alpaca.markets/learn/ccxt-and-alpaca)
