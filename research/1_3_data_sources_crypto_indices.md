# Research 1.3 — Data Sources for Crypto Indices & Individual Assets

> **Task:** Identify the best data sources for crypto indices (`TOTAL`, `TOTAL2`, `TOTAL3`) and individual assets (`BTC`, `ETH`). Evaluate free/freemium APIs (Binance, CoinGecko, CryptoCompare, TradingView unofficial, etc.).

---

## The Core Challenge: TOTAL/TOTAL2/TOTAL3 Are TradingView-Proprietary

**TOTAL, TOTAL2, and TOTAL3 are indices defined and computed by TradingView** under the `CRYPTOCAP` exchange. No major free API natively exposes OHLCV candle data for these exact indices.

| Symbol | Definition |
|--------|-----------|
| `CRYPTOCAP:TOTAL` | Total market cap of top-125 cryptocurrencies |
| `CRYPTOCAP:TOTAL2` | Total market cap of top-125, **excluding BTC** |
| `CRYPTOCAP:TOTAL3` | Total market cap of top-125, **excluding BTC and ETH** |
| `CRYPTOCAP:TOTALES` | Top-125 excluding stablecoins |
| `CRYPTOCAP:TOTAL2ES` | Top-125 excluding BTC and stablecoins |
| `CRYPTOCAP:TOTAL3ES` | Top-125 excluding BTC, ETH, and stablecoins |

This means we have **two separate data problems:**
1. **Individual assets (BTC, ETH)** — easily available from any exchange API
2. **Market cap indices (TOTAL, TOTAL2, TOTAL3)** — require either TradingView scraping or manual computation

---

## Data Sources Evaluated

### 1. Binance (via CCXT)

**What it provides:** OHLCV candles for individual trading pairs (BTC/USDT, ETH/USDT, etc.)

**Free tier:** Fully free, **no API key required** for public market data

| Feature | Detail |
|---------|--------|
| Endpoint | `GET /api/v3/klines` |
| Auth required | No (public market data) |
| Max candles/request | 1,000 |
| Rate limit | 1,200 weight/min (IP-based); each kline call = 2 weight |
| Intervals | 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 1w, 1M |
| Historical depth | Back to 2017-08-17 (spot), 2019-09-08 (futures) |
| Pagination | Loop via startTime/endTime for large datasets |

**Strengths:**
- Completely free, no registration needed
- Most liquid crypto exchange — best price discovery for BTC/ETH
- Excellent via CCXT (`exchange.fetch_ohlcv('BTC/USDT', '1d')`)
- Spot + Futures data available

**Weaknesses:**
- Individual pairs only — no market cap indices
- 1,000-candle pagination required for large fetches
- Geo-restricted (not available in some countries without VPN)

**Verdict:** Best source for BTC, ETH, and other individual asset OHLCV data.

---

### 2. tvDatafeed (Unofficial TradingView Data)

**What it provides:** Historical OHLCV data for **any TradingView symbol**, including `CRYPTOCAP:TOTAL`, `CRYPTOCAP:TOTAL2`, `CRYPTOCAP:TOTAL3`.

**GitHub:** [rongardF/tvdatafeed](https://github.com/rongardF/tvdatafeed) | Multiple active forks exist
**Install:** `pip install git+https://github.com/rongardF/tvdatafeed.git`

| Feature | Detail |
|---------|--------|
| Auth required | Optional (more symbols available with login) |
| Max bars/request | 5,000 |
| Rate limit | Undocumented (TradingView may throttle) |
| Intervals | 1m, 3m, 5m, 15m, 30m, 45m, 1h, 2h, 3h, 4h, 1d, 1w, 1M |
| Returns | Pandas DataFrame with OHLCV columns |

**Usage for TOTAL indices:**
```python
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()  # or TvDatafeed(username, password) for more data
total  = tv.get_hist('TOTAL',  exchange='CRYPTOCAP', interval=Interval.in_daily, n_bars=5000)
total2 = tv.get_hist('TOTAL2', exchange='CRYPTOCAP', interval=Interval.in_daily, n_bars=5000)
total3 = tv.get_hist('TOTAL3', exchange='CRYPTOCAP', interval=Interval.in_daily, n_bars=5000)
```

**Strengths:**
- **Only known way to get OHLCV candles for TOTAL/TOTAL2/TOTAL3 directly**
- Free (no API key needed, though login helps)
- Returns clean Pandas DataFrames
- Supports all TradingView intervals
- Can also fetch BTC, ETH from any exchange on TradingView
- TvDatafeedLive variant supports live data

**Weaknesses:**
- **Unofficial / scraping-based** — can break at any time if TradingView changes internals
- **ToS risk** — may violate TradingView's terms of service
- No official support or SLA
- Multiple competing forks with varying maintenance
- May require TradingView account for certain symbols
- Rate limiting behavior is undocumented and unpredictable

**Verdict:** The only practical way to get TOTAL/TOTAL2/TOTAL3 OHLCV candles. Essential but fragile — should be wrapped in an adapter with fallback logic.

---

### 3. CoinGecko API

**What it provides:** Price, market cap, volume data for 15,000+ coins. Has a global market cap endpoint (paid).

**Free tier (Demo plan):**

| Feature | Detail |
|---------|--------|
| Rate limit | 30 calls/min |
| Monthly cap | 10,000 calls |
| Historical depth | ~1 year |
| OHLCV endpoint | `/coins/{id}/ohlc` — limited intervals (1/7/14/30/90/180/365 days) |
| Market chart | `/coins/{id}/market_chart` — daily/hourly price + market cap |
| Global market cap | `/global` (latest only); historical = **paid only** |
| Auth | API key required |

**Key endpoints:**
- `/coins/{id}/ohlc` — OHLC candles (no volume), limited to predefined day ranges
- `/coins/{id}/market_chart` — price, market cap, volume time series (not true OHLCV candles)
- `/global` — current total market cap (not historical)
- `/global/market_cap_chart` — historical total market cap (💼 **paid plans only**, starting at $129/mo)

**Strengths:**
- Covers 15,000+ coins with market cap data
- Free tier is generous for basic use (30 calls/min)
- Good for getting individual coin market caps to compute TOTAL2/TOTAL3 manually
- Data back to 2013 on paid plans

**Weaknesses:**
- **No true OHLCV candles** on the market chart endpoint (gives price + market cap points, not OHLC)
- **Historical global market cap is paid-only** ($129+/mo)
- OHLC endpoint has rigid day-range options (no arbitrary date ranges)
- Free tier limited to 1 year of history and 10k calls/month
- REST-only, no WebSocket
- Cached data (1–5 min delay on free tier)

**Verdict:** Useful as a supplementary source for coin metadata, market caps, and as a fallback. Not suitable as primary OHLCV source — too limited on free tier.

---

### 4. CryptoCompare (CCData)

**What it provides:** Historical OHLCV data for 5,700+ coins across 260,000+ trading pairs and 170+ exchanges.

**Free tier:**

| Feature | Detail |
|---------|--------|
| Rate limit | Varies (API key required) |
| Historical depth | Back to 2010 for BTC |
| Daily/Hourly OHLCV | Available on free tier |
| Minute OHLCV | Enterprise only (beyond 7 days) |
| Pairs | 260,000+ across 170+ exchanges |
| Auth | API key required |

**Key endpoints:**
- `histoday` — daily OHLCV
- `histohour` — hourly OHLCV
- `histominute` — minute OHLCV (7-day limit on free, full on enterprise)

**Strengths:**
- One of the oldest crypto data providers (since 2014)
- Extensive historical coverage back to 2010
- Free daily/hourly OHLCV with generous limits
- Exchange-specific or aggregate data available
- Covers many obscure/smaller coins

**Weaknesses:**
- Minute data beyond 7 days requires enterprise ($$$)
- No TOTAL/TOTAL2/TOTAL3 indices
- Rebranded to CCData — documentation can be confusing
- Paid plans start at $80/mo for commercial use
- No WebSocket on free tier

**Verdict:** Good alternative to Binance for individual asset OHLCV, especially for historical depth. No help with market cap indices.

---

### 5. CoinMarketCap API

**What it provides:** Crypto rankings, pricing, market data from the world's most visited crypto site.

**Free tier (Basic plan):**

| Feature | Detail |
|---------|--------|
| Endpoints | 9 market data endpoints |
| Monthly cap | 10,000 calls |
| Historical OHLCV | **Not available** (requires Startup plan, $79/mo) |
| Global market cap | Latest only; historical = **paid only** |
| Auth | API key required |

**Strengths:**
- Most widely recognized crypto data brand
- Latest pricing and market cap data on free tier
- Extensive coin coverage

**Weaknesses:**
- **No historical OHLCV on free tier** — requires $79/mo minimum
- **No historical global market cap on free tier**
- Very limited free plan (only 9 endpoints)
- Not suitable for our use case without paid subscription

**Verdict:** Not recommended. Free tier is too restricted for our needs. No historical data without paying.

---

### 6. Other TradingView Unofficial Libraries

| Library | Type | TOTAL Support | Notes |
|---------|------|--------------|-------|
| **tradingview-ta** | TA signals | **No** — indices not supported (issues #67, #84) | Only for TA summaries, not OHLCV |
| **tradingView-API** (mohamadkhalaj) | WebSocket | Maybe — supports `'index'` category | Real-time data via TradingView socket |
| **tradingview-screener** | Screener | Crypto screener available | Not for historical OHLCV candles |
| **Apify TradingView scraper** | Commercial scraper | Yes | Paid service, API/MCP access |

---

### 7. Other Notable Data Sources

| Source | Free Tier | Individual Assets | Market Cap Indices | Notes |
|--------|-----------|-------------------|-------------------|-------|
| **CryptoDataDownload** | Free CSV downloads | Yes | No | Good for bulk historical downloads |
| **Alpha Vantage** | 25 calls/day | Yes (crypto + stocks) | No | Too rate-limited for production |
| **Polygon.io** | Limited free | Stocks/forex/crypto | No | $29+/mo for useful access |
| **Tiingo** | 500 requests/hour | Stocks + crypto | No | Good free tier for stocks |
| **Alpaca** | Free | US stocks + crypto | No | Trading-focused; has CCXT integration |

---

## Comparison Matrix

| Criteria | Binance (CCXT) | tvDatafeed | CoinGecko | CryptoCompare | CoinMarketCap |
|----------|---------------|------------|-----------|---------------|---------------|
| **BTC/ETH OHLCV** | Excellent | Good | Limited | Excellent | Paid only |
| **TOTAL/TOTAL2/TOTAL3** | No | **Yes** | No (paid global) | No | No (paid global) |
| **Free tier quality** | Excellent | Free/unofficial | Decent | Good | Poor |
| **Historical depth** | 2017+ | Depends on TV data | 1yr free / 12yr paid | 2010+ | Paid only |
| **Reliability** | High (official API) | Low (unofficial) | Medium | High | Medium |
| **Rate limits** | 600 calls/min | Unknown | 30 calls/min | Varies | 10k/month |
| **Auth required** | No | Optional | Yes (API key) | Yes (API key) | Yes (API key) |
| **CCXT integration** | Native | No | No | No | No |
| **Candle intervals** | All standard | All standard | Rigid presets | Daily/hourly/min | Paid tiers vary |

---

## Recommendation

### For Individual Assets (BTC, ETH, etc.): **Binance via CCXT**

**Rationale:**
1. Completely free, no API key needed for public market data
2. Most liquid exchange = best price discovery
3. CCXT provides a clean, exchange-agnostic interface (aligns with 1.1 recommendation)
4. Generous rate limits (600 kline calls/min)
5. All standard intervals from 1m to 1M
6. Historical data back to 2017

If Binance is unavailable (geo-restriction, outage), CCXT makes switching to Bybit, Kraken, or OKX a config change.

### For Market Cap Indices (TOTAL, TOTAL2, TOTAL3): **tvDatafeed**

**Rationale:**
1. **Only known free method** to get OHLCV candles for TradingView's CRYPTOCAP indices
2. Direct access to the exact TOTAL/TOTAL2/TOTAL3 data that traders reference
3. Returns clean Pandas DataFrames
4. Supports all timeframes needed (5m through 1M)

**Risk mitigation:**
- Wrap tvDatafeed in an adapter behind our market data port (from Phase 2 architecture)
- Implement caching (Phase 4.4) to reduce API calls and survive temporary outages
- Build a fallback: compute approximate TOTAL2/TOTAL3 from individual coin market caps via CoinGecko if tvDatafeed breaks

### Supplementary: **CoinGecko** (free tier)

Use CoinGecko's free API for:
- Coin metadata (names, categories, market cap rankings)
- Fallback market cap data for computing approximate TOTAL2/TOTAL3
- Cross-referencing / data validation

### Not recommended:
- **CoinMarketCap** — free tier too restrictive, no historical data
- **CryptoCompare** — good data but adds complexity without solving the TOTAL index problem; Binance via CCXT already covers individual assets well
- **Alpha Vantage** — 25 calls/day is unusable for production

### Architecture implication:

The data layer should define an abstract `MarketDataProvider` interface (port) with at least two concrete adapters:
1. **ExchangeDataAdapter** (Binance via CCXT) — for individual asset OHLCV
2. **IndexDataAdapter** (tvDatafeed) — for TOTAL/TOTAL2/TOTAL3 OHLCV
3. Optional: **CoinGeckoAdapter** — for metadata and fallback market cap data

This aligns with the DDD approach planned in Phase 2 and the plugin architecture from task 2.5.

---

## Sources

- [TradingView CRYPTOCAP:TOTAL Index Chart](https://www.tradingview.com/symbols/TOTAL/)
- [TradingView — How CRYPTOCAP Symbols Are Calculated](https://www.tradingview.com/support/solutions/43000550480-how-are-the-cryptocap-symbols-calculated/)
- [tvDatafeed GitHub (rongardF)](https://github.com/rongardF/tvdatafeed)
- [tvDatafeed Guide — Oreate AI](https://www.oreateai.com/blog/unlocking-market-insights-with-tvdatafeed-a-comprehensive-guide/6fe6313c9074f2f83c402bea2d3154e9)
- [tvDatafeed Guide — Computer Aided Automation](https://computeraidedautomation.com/infusions/articles/articles.php?article_id=137)
- [Binance Market Data Endpoints](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints)
- [Binance Kline Candlestick Data](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data)
- [CoinGecko API](https://www.coingecko.com/en/api)
- [CoinGecko Global Market Cap Chart Endpoint](https://docs.coingecko.com/reference/global-market-cap-chart)
- [CoinGecko API Pricing](https://www.coingecko.com/en/api/pricing)
- [CoinGecko Best Historical Crypto Data APIs (2026)](https://www.coingecko.com/learn/best-historical-crypto-data-apis)
- [CryptoCompare API Pricing](https://min-api.cryptocompare.com/pricing)
- [CryptoCompare API Guide](https://www.cryptocompare.com/coins/guides/how-to-use-our-api/)
- [CoinMarketCap API Pricing](https://coinmarketcap.com/api/pricing/)
- [CoinMarketCap API Documentation](https://coinmarketcap.com/api/documentation/v1/)
- [CoinMarketCap API FAQ](https://coinmarketcap.com/api/faq/)
- [Top 5 Cryptocurrency Data APIs Comparison (2025) — Medium/Coinmonks](https://medium.com/coinmonks/top-5-cryptocurrency-data-apis-comprehensive-comparison-2025-626450b7ff7b)
- [tradingview-ta on PyPI](https://pypi.org/project/tradingview-ta/)
- [tradingView-API (mohamadkhalaj) GitHub](https://github.com/mohamadkhalaj/tradingView-API)
- [CryptoDataDownload](https://www.cryptodatadownload.com/data/)
