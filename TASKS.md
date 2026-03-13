# Crypto Signal App — Task Plan

## Phase 1: Research & Technology Selection ✅
- [x] **1.1** Research and select the best Python libraries for fetching market data (OHLCV) across crypto (and later forex/stocks). Compare `ccxt`, `python-binance`, and alternatives. → **Selected: `ccxt`**
- [x] **1.2** Research and select the best technical analysis library for computing indicators and divergences. Compare `pandas-ta`, `ta-lib`, `ta`, and alternatives. → **Selected: `pandas-ta`**
- [x] **1.3** Identify the best data sources for crypto indices (`TOTAL`, `TOTAL2`, `TOTAL3`) and individual assets (`BTC`, `ETH`). Evaluate free/freemium APIs (Binance, CoinGecko, CryptoCompare, TradingView unofficial, etc.). → **Selected: Binance (primary) + CoinGecko (indices)**
- [x] **1.4** Research SMT (Smart Money Technique) divergence calculation: definition, required data, detection algorithm between correlated assets. → **Documented: pivot-based swing detection + time-aligned comparison**
- [x] **1.5** Evaluate UI/interface options that require zero frontend/styling effort. Compare Streamlit, Gradio, Textual (TUI), CLI with `rich`/`typer`. → **Selected: Streamlit (primary) + Rich/Typer (CLI)**
- [x] **1.6** Evaluate signal delivery channels: Telegram bot, Discord webhook, email. Select libraries. → **Selected: `apprise` (unified)**
- [x] **1.7** Evaluate scheduling/orchestration tools for periodic signal checks (`APScheduler`, `Celery`, cron-based). → **Selected: `APScheduler 3.x`**

## Phase 2: Architecture & Domain Design (DDD)
- [ ] **2.1** Define bounded contexts: Market Data, Signal Engine, Notification, Configuration.
- [ ] **2.2** Define domain entities, value objects, and aggregates (Asset, Timeframe, Signal, Divergence, MarketData, etc.).
- [ ] **2.3** Define domain events (e.g., `DivergenceDetected`, `SignalEmitted`).
- [ ] **2.4** Design the plugin/modular system for strategies and indicators (registry pattern, abstract base classes or Protocols) so adding a new signal is as simple as dropping a file.
- [ ] **2.5** Design the market abstraction layer so crypto, forex, and stocks can be swapped by changing the data provider.
- [ ] **2.6** Design the configuration system (YAML/TOML) for selecting timeframes, asset pairs, and signal parameters at runtime.
- [ ] **2.7** Produce the final project directory structure and document it.

## Phase 3: Core Domain Implementation
- [ ] **3.1** Set up the project skeleton: folder structure, `pyproject.toml`, dependencies.
- [ ] **3.2** Implement core value objects and entities (`Asset`, `Timeframe`, `OHLCV`, `Signal`, `Divergence`).
- [ ] **3.3** Implement the domain event bus (in-process pub/sub for signal propagation).
- [ ] **3.4** Implement the signal/strategy plugin registry and base protocol.

## Phase 4: Data Layer (Infrastructure)
- [ ] **4.1** Implement the market data provider interface (port).
- [ ] **4.2** Implement the crypto data adapter (using the library chosen in Phase 1).
- [ ] **4.3** Implement data fetching for crypto indices (`TOTAL`, `TOTAL2`, `TOTAL3`).
- [ ] **4.4** Implement local caching/storage for historical data to avoid redundant API calls.

## Phase 5: First Signal — SMT Divergence
- [ ] **5.1** Implement the SMT divergence detection algorithm (swing high/low comparison between correlated assets).
- [ ] **5.2** Register it as a pluggable signal under the strategy registry.
- [ ] **5.3** Support configurable asset pairs (BTC vs ETH, BTC vs TOTAL, BTC vs TOTAL2, BTC vs TOTAL3, etc.).
- [ ] **5.4** Support configurable multi-timeframe analysis (1D, 4H, 15m, 5m, etc.).

## Phase 6: Signal Orchestration & Scheduling
- [ ] **6.1** Implement the signal engine that runs registered strategies on a schedule.
- [ ] **6.2** Implement configurable scheduling (e.g., check every candle close per timeframe).
- [ ] **6.3** Implement signal deduplication (avoid emitting the same divergence repeatedly).

## Phase 7: Notification / Delivery
- [ ] **7.1** Implement the notification port (abstract interface).
- [ ] **7.2** Implement at least one adapter: Telegram bot or Discord webhook.
- [ ] **7.3** Format signal output with relevant context (pair, timeframe, divergence type, chart reference).

## Phase 8: User Interface
- [ ] **8.1** Build a lightweight UI (chosen in Phase 1) for:
  - Viewing active signals and history.
  - Configuring timeframes and asset pairs.
  - Starting/stopping the signal engine.
- [ ] **8.2** Display basic charts or divergence visualizations if feasible within the chosen tool.

## Phase 9: Testing & Validation
- [ ] **9.1** Unit tests for domain logic (divergence detection, value objects).
- [ ] **9.2** Integration tests for data providers (with mocked responses).
- [ ] **9.3** Manual validation with real market data on at least one timeframe.

## Phase 10: Documentation & Deployment
- [ ] **10.1** Write a README with setup instructions, configuration guide, and how to add a new signal.
- [ ] **10.2** Provide a Docker setup for easy deployment.
- [ ] **10.3** Document the plugin guide: "How to add a new indicator/strategy in 3 steps."

---

> **Next step:** Begin Phase 2 — Architecture & Domain Design (DDD), one task at a time.
