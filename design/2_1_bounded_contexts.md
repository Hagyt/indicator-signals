# Design 2.1 — Bounded Contexts

> **Task:** Define bounded contexts: Market Data, Signal Engine, Notification, Configuration.

---

## Overview

Following Domain-Driven Design (DDD) principles, the system is decomposed into four bounded contexts. Each context has clear responsibilities, its own ubiquitous language, and well-defined boundaries. Communication between contexts happens through domain events and explicit interfaces (ports).

---

## Bounded Context Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CONFIGURATION CONTEXT                           │
│                                                                        │
│  Owns: App settings, asset pair definitions, timeframe selections,     │
│        scan intervals, notification channel config, strategy params    │
│                                                                        │
│  Reads: YAML/TOML config files                                        │
│  Publishes: ConfigLoaded, ConfigUpdated                                │
└────────────┬────────────────────────────┬───────────────────────────────┘
             │ provides config to          │ provides config to
             ▼                             ▼
┌──────────────────────────┐   ┌──────────────────────────────────────────┐
│   MARKET DATA CONTEXT    │   │          SIGNAL ENGINE CONTEXT           │
│                          │   │                                          │
│  Owns: OHLCV data,       │   │  Owns: Signal detection, divergence     │
│  exchange connections,    │   │  algorithms, strategy plugins,          │
│  index data, caching     │   │  scheduling, signal lifecycle           │
│                          │   │                                          │
│  Adapters:               │   │  Consumes: MarketData (from Market Data │
│  - ExchangeAdapter(CCXT) │   │            Context via port)             │
│  - IndexAdapter(tvData)  │   │  Publishes: SignalDetected,             │
│  - CoinGeckoAdapter      │   │    DivergenceDetected, SignalInvalidated│
│                          │   │                                          │
│  Publishes:              │   │  Plugins: SMT Divergence, RSI Div,     │
│    MarketDataFetched     │   │    future strategies...                  │
└──────────┬───────────────┘   └─────────────────┬────────────────────────┘
           │                                     │
           │ provides OHLCV                      │ emits signal events
           └──────────►┘                         ▼
                                    ┌──────────────────────────────────┐
                                    │    NOTIFICATION CONTEXT          │
                                    │                                  │
                                    │  Owns: Message formatting,       │
                                    │  delivery routing, channel mgmt  │
                                    │                                  │
                                    │  Consumes: Signal events         │
                                    │  Adapters:                       │
                                    │  - Apprise (Telegram, Discord,   │
                                    │    Email, 90+ services)          │
                                    │                                  │
                                    │  Publishes:                      │
                                    │    NotificationSent,             │
                                    │    NotificationFailed            │
                                    └──────────────────────────────────┘
```

---

## 1. Configuration Context

**Responsibility:** Owns all runtime configuration — what to scan, how often, where to send alerts, and with what parameters.

**Ubiquitous Language:**
- **Config Profile** — a complete set of application settings
- **Asset Pair** — two correlated assets to compare (e.g., BTC/USDT vs ETH/USDT)
- **Scan Schedule** — interval or cron expression for when to run a strategy
- **Strategy Parameters** — settings specific to a signal strategy (e.g., pivot lookback, max swing distance)
- **Notification Target** — a configured delivery channel (Telegram, Discord, etc.)

**Owns:**
- YAML/TOML config file parsing and validation
- Asset pair definitions (asset A, asset B, correlation type)
- Timeframe selections (1D, 4H, 1H, 15m, 5m)
- Scan intervals per strategy/timeframe
- Notification channel URLs and routing rules (tags)
- Strategy-specific parameter overrides

**Key Rules:**
- Config is loaded at startup and can be reloaded at runtime
- All other contexts receive their configuration from this context — they never read config files directly
- Config validation happens here: invalid pairs, unknown strategies, malformed URLs are rejected at load time

**Interfaces (Ports):**
- `ConfigProvider` — read-only interface for other contexts to query configuration
- Events: `ConfigLoaded`, `ConfigUpdated`

**Technology:**
- YAML or TOML files (human-editable)
- Pydantic models for validation and type safety

---

## 2. Market Data Context

**Responsibility:** Fetches, normalizes, caches, and serves OHLCV market data from external sources. Acts as the single source of truth for price data within the system.

**Ubiquitous Language:**
- **OHLCV** — Open, High, Low, Close, Volume candle data
- **Asset** — a tradable instrument identified by symbol (e.g., BTC/USDT) or index (e.g., TOTAL)
- **Timeframe** — candle interval (1m, 5m, 15m, 1H, 4H, 1D, 1W)
- **Data Provider** — an external source of market data (exchange, index service)
- **Candle** — a single OHLCV data point for a specific timestamp and timeframe

**Owns:**
- Exchange connections and API interactions
- OHLCV data fetching, pagination, and rate limit management
- Data normalization (different providers → uniform OHLCV format)
- Local caching/storage to avoid redundant API calls
- Index data fetching (TOTAL, TOTAL2, TOTAL3 via tvDatafeed)

**Key Rules:**
- All OHLCV data returned to consumers is in a normalized format regardless of source
- Candles are time-aligned (UTC timestamps)
- Caching is transparent — consumers don't know if data came from cache or API
- Provider failures are handled internally (retry, fallback) before surfacing errors

**Interfaces (Ports):**
- `MarketDataProvider` (inbound port) — abstract interface for fetching OHLCV data
  - `fetch_ohlcv(asset, timeframe, since, limit) → list[Candle]`
- `MarketDataCache` (outbound port) — abstract interface for caching

**Adapters (Infrastructure):**
- `CcxtExchangeAdapter` — fetches individual asset OHLCV via CCXT (Binance primary)
- `TvDatafeedIndexAdapter` — fetches TOTAL/TOTAL2/TOTAL3 via tvDatafeed
- `CoinGeckoAdapter` — supplementary metadata and fallback market cap data
- `LocalCacheAdapter` — SQLite or file-based cache for historical data

**Events:**
- `MarketDataFetched` — emitted when fresh data is successfully retrieved

---

## 3. Signal Engine Context

**Responsibility:** The core domain. Runs signal detection strategies against market data, manages signal lifecycle, and orchestrates scheduled scans. This is where the business logic lives.

**Ubiquitous Language:**
- **Signal** — a detected trading opportunity (e.g., bearish SMT divergence on BTC/ETH 4H)
- **Divergence** — a specific type of signal where correlated assets' swing structures disagree
- **Strategy** — a pluggable algorithm that analyzes market data and produces signals
- **Swing Point** — a local price extremum (swing high or swing low)
- **Pivot** — a confirmed swing point (confirmed after right lookback bars)
- **Scan** — a single execution of a strategy against a specific asset pair and timeframe
- **Signal Lifecycle** — Active → Invalidated or Active → Expired

**Owns:**
- Strategy plugin registry (register, discover, instantiate strategies)
- Swing point / pivot detection algorithms
- SMT divergence detection algorithm
- Signal creation, scoring, deduplication, and invalidation
- Scheduled scan orchestration (via APScheduler)
- Multi-timeframe analysis coordination

**Key Rules:**
- Strategies are pluggable — adding a new signal type means dropping a new file implementing the `Strategy` protocol
- The engine requests data from Market Data Context through the `MarketDataProvider` port — it never fetches data directly
- Signals are deduplicated — the same divergence is not emitted repeatedly
- Signals have lifecycle: they can be invalidated when price exceeds a threshold
- Multi-timeframe: a signal on a higher timeframe is stronger than the same signal on a lower timeframe

**Interfaces (Ports):**
- `Strategy` (protocol) — interface that all signal strategies must implement
  - `analyze(market_data) → list[Signal]`
- `StrategyRegistry` — register and retrieve available strategies
- Depends on: `MarketDataProvider` (from Market Data Context)
- Depends on: `ConfigProvider` (from Configuration Context)

**Events:**
- `SignalDetected` — a new signal has been identified
- `DivergenceDetected` — specifically an SMT or indicator divergence signal
- `SignalInvalidated` — a previously active signal has been invalidated by price action

**Technology:**
- APScheduler 3.x (BackgroundScheduler) for scan orchestration
- Custom pivot detection algorithm
- Strategy registry pattern with abstract base classes or Protocols

---

## 4. Notification Context

**Responsibility:** Receives signal events from the Signal Engine Context, formats them into human-readable messages, and delivers them through configured channels.

**Ubiquitous Language:**
- **Notification** — a formatted message ready for delivery
- **Channel** — a delivery mechanism (Telegram, Discord, Email, etc.)
- **Formatter** — transforms a domain event into a channel-appropriate message
- **Routing** — rules for which signals go to which channels (tag-based)

**Owns:**
- Message formatting (converting Signal/Divergence domain objects into readable text)
- Channel-specific formatting (Telegram markdown, Discord embeds, email HTML)
- Delivery routing (tag-based: critical → Telegram + Discord, summaries → email)
- Delivery status tracking (sent, failed, retried)

**Key Rules:**
- Notification Context is a pure consumer of events — it never triggers scans or modifies signals
- Formatting is separated from delivery — different formatters for different channels
- Failed deliveries are retried with backoff
- Notification URLs/credentials come from Configuration Context

**Interfaces (Ports):**
- `NotificationSender` (outbound port) — abstract interface for sending notifications
  - `send(message, channels) → DeliveryResult`
- `SignalFormatter` — transforms domain events into formatted messages
- Depends on: `ConfigProvider` (from Configuration Context) for channel URLs

**Adapters (Infrastructure):**
- `AppriseNotificationAdapter` — unified delivery via Apprise (90+ services)
- Optional future: `DiscordWebhookAdapter` (rich embeds), `TelegramBotAdapter` (interactive)

**Events:**
- `NotificationSent` — delivery confirmed
- `NotificationFailed` — delivery failed (triggers retry or alert)

---

## Context Communication Patterns

### Event Flow (Primary)

```
Configuration ──config──► Signal Engine ──signal events──► Notification
                              │
                              │ requests data
                              ▼
                          Market Data
```

### Communication Mechanisms

| From → To | Mechanism | Notes |
|-----------|-----------|-------|
| Configuration → All | Direct dependency injection | Config is passed at startup/reload |
| Market Data → Signal Engine | Synchronous method call (port) | Engine calls `fetch_ohlcv()` when needed |
| Signal Engine → Notification | Domain events (in-process pub/sub) | Async, decoupled |
| Signal Engine → Signal Engine | Internal (scheduler → strategy) | APScheduler triggers scans |

### Anti-Corruption Layers

| Boundary | ACL Purpose |
|----------|-------------|
| Market Data ↔ External APIs | Normalize diverse API responses into uniform `Candle` format |
| Notification ↔ Apprise | Translate domain `Signal` into Apprise notification format |
| Configuration ↔ YAML files | Validate and type-check raw config into domain models |

---

## Directory Structure Preview

```
src/
├── config/              # Configuration Context
│   ├── models.py        # Pydantic config models
│   ├── loader.py        # YAML/TOML loader
│   └── provider.py      # ConfigProvider implementation
│
├── market_data/         # Market Data Context
│   ├── ports.py         # MarketDataProvider interface
│   ├── models.py        # Candle, Asset, Timeframe
│   ├── adapters/
│   │   ├── ccxt_adapter.py
│   │   ├── tvdatafeed_adapter.py
│   │   └── cache_adapter.py
│   └── service.py       # Orchestrates fetching + caching
│
├── signal_engine/       # Signal Engine Context
│   ├── ports.py         # Strategy protocol, StrategyRegistry
│   ├── models.py        # Signal, Divergence, SwingPoint
│   ├── detection/
│   │   ├── swing.py     # Pivot/swing detection algorithm
│   │   └── smt.py       # SMT divergence strategy
│   ├── registry.py      # Strategy plugin registry
│   ├── scheduler.py     # APScheduler integration
│   └── service.py       # Signal engine orchestration
│
├── notification/        # Notification Context
│   ├── ports.py         # NotificationSender interface
│   ├── formatters.py    # Signal → message formatting
│   ├── adapters/
│   │   └── apprise_adapter.py
│   └── service.py       # Notification orchestration
│
└── shared/              # Shared Kernel (minimal)
    ├── events.py        # Domain event base class + event bus
    └── types.py         # Shared types (if any)
```

---

## Shared Kernel

A minimal shared kernel contains only what is truly shared across all contexts:

- **Event base class** — `DomainEvent` with timestamp, event_id
- **Event bus** — in-process pub/sub for domain event propagation
- **Common types** — only if genuinely shared (e.g., `AssetSymbol` type alias)

**Rule:** Keep the shared kernel as small as possible. If something is only used by two contexts, it belongs in one of them and is exposed through its port.
