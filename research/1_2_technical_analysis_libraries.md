# Research 1.2 — Technical Analysis Libraries for Indicators & Divergences

> **Task:** Research and select the best technical analysis library for computing indicators and divergences. Compare `pandas-ta`, `ta-lib`, `ta`, and alternatives.

---

## Libraries Evaluated

### 1. TA-Lib (via `ta-lib-python`)

**What it is:** The industry-standard C library for technical analysis (since 2001), with a Python wrapper using Cython + NumPy for high-performance vectorized computation.

**GitHub:** ~10k stars (python wrapper) | BSD License
**PyPI:** `TA-Lib` — latest v0.6.8 (Oct 2025) | Wheels for CPython 3.12–3.14
**Core language:** C/C++ with Python, R, Ruby, Zig wrappers

**Indicators:** 200+ indicators + candlestick pattern recognition, organized into:
- Momentum: ADX, MACD, RSI, Stochastic, CCI, MFI, ROC, Williams %R
- Overlap Studies: SMA, EMA, WMA, DEMA, TEMA, Bollinger Bands, SAR, KAMA
- Volume: OBV, AD, ADOSC
- Volatility: ATR, NATR, True Range
- Candlestick Patterns: 60+ patterns (Doji, Engulfing, Hammer, Harami, etc.)
- Math Transform/Operators: vector math functions

**APIs:**
- **Function API** — lightweight, direct function calls: `talib.RSI(close, timeperiod=14)`
- **Abstract API** — dictionary-based input, same indicators
- **Streaming API** (experimental) — compute only the latest value for real-time use

**Strengths:**
- Fastest batch computation — C implementation, 2–4x faster than SWIG bindings
- Battle-tested for 20+ years, stable and well-understood algorithms
- Supports Pandas DataFrames and Polars DataFrames natively
- Pre-built binary wheels since v0.6.5 (greatly simplifies installation)
- Comprehensive candlestick pattern recognition (unique advantage)
- Healthy maintenance — active releases, 40+ contributors, no known vulnerabilities

**Weaknesses:**
- **Installation complexity** — historically painful (requires C library). Binary wheels have improved this but edge cases remain (Windows path spaces, architecture mismatches)
- **Version fragmentation** — three branches: 0.4.x (numpy 1), 0.5.x (numpy 2 + old C lib), 0.6.x (numpy 2 + new C lib)
- **No incremental/streaming computation** — recalculates entire array; O(n) for each update
- **No built-in divergence detection** — provides raw indicators only; swing high/low and divergence logic must be custom-built
- **No GIL-free mode support** yet (open issue for Python 3.13+)
- **C source code is hard to read** — debugging indicator internals is difficult

**OHLCV Usage Example:**
```python
import talib
import numpy as np

close = np.array(df['close'])
rsi = talib.RSI(close, timeperiod=14)
macd, signal, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
upper, middle, lower = talib.BBANDS(close, timeperiod=20)
```

---

### 2. pandas-ta

**What it is:** A Python 3 Pandas Extension providing 150+ technical analysis indicators, leveraging NumPy and Numba for performance.

**GitHub:** ~6,064 stars (original repo by twopirllc — now removed from GitHub)
**PyPI:** `pandas-ta` — latest v0.4.71b0 (beta)
**License:** MIT

**Critical maintenance status:** The original author removed the repository from GitHub. Unless significant support is provided by **July 1, 2026**, the library will be archived. Current support levels described as "unsustainable."

**Active fork:** `pandas-ta-classic` (by xgboosted) — 200+ indicators, latest release v0.3.78 (Feb 27, 2026), 200 stars, 44 contributors. Actively maintained.

**Indicators:** 150+ indicators (200+ in the classic fork) plus 60 candlestick patterns when TA-Lib is installed.

**Strengths:**
- Seamless Pandas integration — call indicators directly on DataFrames via `.ta` extension
- Pure Python — no C dependency, easy installation
- Uses Numba for JIT compilation where possible
- Large indicator set without TA-Lib; even more with TA-Lib installed
- Highly correlated with TA-Lib output (verified)
- Strategy helper for applying multiple indicators at once

**Weaknesses:**
- **Maintenance crisis** — original repo removed, sustainability at risk
- **Still in beta** (v0.4.71b0) after years of development
- **Slower than TA-Lib** — operates on DataFrames rather than raw NumPy vectors
- **No built-in divergence detection** — indicators only
- **No incremental computation** — full recalculation on each call
- Fork landscape is fragmented (pandas-ta-classic, pandas-ta-fork, etc.)

**Usage Example:**
```python
import pandas_ta as ta

df.ta.rsi(length=14, append=True)
df.ta.macd(fast=12, slow=26, signal=9, append=True)
df.ta.bbands(length=20, append=True)
# Or apply a strategy:
df.ta.strategy("Momentum")
```

---

### 3. ta (by bukosabino)

**What it is:** A lightweight Technical Analysis library for feature engineering from financial time series, built on Pandas and NumPy.

**GitHub:** ~4,800 stars | ~1,100 forks | MIT License
**PyPI:** `ta` — latest v0.11.0 (Nov 2, 2023)
**Downloads:** ~578k/month

**Indicators:** 43 indicators organized into 5 groups:
- Momentum: RSI, Stochastic, Williams %R, Awesome Oscillator, ROC, StochRSI, KAMA
- Volume: OBV, MFI, ADI, CMF, Force Index, VPT
- Volatility: Bollinger Bands, Keltner Channel, Donchian Channel, ATR
- Trend: MACD, EMA, SMA, ADX, Ichimoku, Aroon, CCI
- Others: Daily Return, Cumulative Return

**Strengths:**
- Very simple API — `add_all_ta_features()` adds 80+ columns in one call
- Pure Python — no C dependency, trivial to install
- Good for quick feature engineering / ML pipelines
- Clean class-based API: `ta.momentum.RSIIndicator(close, window=14)`
- Still widely downloaded despite lack of updates

**Weaknesses:**
- **Unmaintained** — no releases since Nov 2023, open bugs unanswered through 2024–2025
- **Only 43 indicators** — significantly fewer than TA-Lib or pandas-ta
- **No candlestick patterns**
- **No divergence detection or swing high/low**
- **No incremental computation**
- Performance not optimized — pure Pandas operations
- Bugs reported in 2024 remain unfixed (e.g., issue #336)

**Usage Example:**
```python
from ta.momentum import RSIIndicator
from ta.trend import MACD

rsi = RSIIndicator(close=df['close'], window=14).rsi()
macd = MACD(close=df['close']).macd()
```

---

### 4. talipp (Incremental TA)

**What it is:** A Python library for incremental (streaming) technical analysis — calculates new indicator values based only on delta input, achieving O(1) time for updates.

**GitHub:** [nardew/talipp](https://github.com/nardew/talipp) | MIT License
**PyPI:** `talipp` — latest v2.7.0

**Strengths:**
- **O(1) incremental updates** vs O(n) for all other libraries — ideal for real-time streaming
- Indicator chaining — compose indicators from other indicators
- CUD (Create/Update/Delete) operations on input data reflected instantly
- Scales linearly with input size for incremental operations (vs quadratic for batch libs)
- Batch processing of 50k values still achievable in ~200ms
- Pure Python — no C dependency

**Weaknesses:**
- Slower than TA-Lib for one-shot batch computation (expected: Python vs C)
- Smaller indicator set than TA-Lib or pandas-ta
- Smaller community / ecosystem
- No built-in divergence detection
- Less battle-tested than TA-Lib

**Best for:** Real-time applications receiving streaming data where you need updated indicator values with each new candle/tick.

---

### 5. FinTA (Financial Technical Analysis)

**What it is:** Common financial technical indicators implemented in Pandas.

**GitHub:** ~2,124 stars | [peerchemist/finta](https://github.com/peerchemist/finta) | LGPL License
**PyPI:** `finta`

**Indicators:** ~75 indicators including:
- Moving Averages: DEMA, TEMA, ZLEMA, FRAMA, and more
- Oscillators: StochRSI, Williams %R, Ultimate Oscillator
- Support/Resistance: Pivot Points
- Volume: OBV, MFI, VWAP

**Strengths:**
- Simple API: `TA.RSI(df)`, `TA.MACD(df)`
- Pure Python — easy install
- Good selection of lesser-known indicators
- Includes Pivot Points (support/resistance)

**Weaknesses:**
- Self-described as "work in progress — bugs expected, results may not be accurate"
- LGPL license (more restrictive than MIT/BSD)
- No divergence detection
- Smaller community than top-tier options
- Accuracy not guaranteed by maintainer

---

### 6. ta-py

**What it is:** A lightweight technical analysis library with **built-in divergence detection**.

**PyPI:** `ta-py`

**Unique feature — Divergence Detection:**
- `ta.rsi_divergence(data, rsi_length, rsi_function)` — outputs array: `1 = divergence`, `0 = no divergence`
- `ta.divergence(data1, data2)` — general divergence comparison between any two data series

**Strengths:**
- Only library found with built-in RSI divergence detection
- General-purpose divergence function for any two series
- Lightweight

**Weaknesses:**
- Very small community and limited documentation
- Limited indicator set compared to major libraries
- Not widely adopted or battle-tested
- May not be production-quality

---

### 7. Other Notable Alternatives

| Library | Stars | Key Differentiator | Limitation |
|---------|-------|--------------------|------------|
| **stockstats** | ~1.2k | Inline DataFrame stats, cross-over detection | No divergence detection |
| **tulipy** | ~400 | Python wrapper for Tulip Indicators (C) | Small community, less maintained |
| **bta-lib** | ~400 | Easy-to-read indicators, simple creation of new ones | Small community |
| **Backtrader** | ~14k | Full backtesting framework with built-in indicators | Overkill if you only need indicators |
| **PyIndicators** | ~20 | Pandas + Polars support, no external deps | Very new, minimal adoption |

---

## Comparison Matrix

| Criteria | TA-Lib | pandas-ta | ta (bukosabino) | talipp | FinTA | ta-py |
|----------|--------|-----------|-----------------|--------|-------|-------|
| **Indicator count** | 200+ | 150+ (200+ classic) | 43 | ~50 | ~75 | ~30 |
| **Candlestick patterns** | 60+ | 60 (via TA-Lib) | No | No | No | No |
| **Performance** | Fastest (C) | Good (Numba) | Moderate | O(1) incremental | Moderate | Moderate |
| **Divergence detection** | No | No | No | No | No | **Yes** |
| **Swing high/low** | No | No | No | No | No | No |
| **Pandas integration** | Yes | Native extension | Yes | No (own types) | Yes | No |
| **Installation ease** | Moderate (wheels help) | Easy (pip) | Easy (pip) | Easy (pip) | Easy (pip) | Easy (pip) |
| **Maintenance** | Active | At risk (July 2026) | Unmaintained | Active | Low activity | Low activity |
| **Incremental updates** | No (batch only) | No | No | **Yes (O(1))** | No | No |
| **License** | BSD | MIT | MIT | MIT | LGPL | MIT |
| **Community** | Very large | Large (fragmented) | Large (passive) | Small | Medium | Very small |

---

## Relevance to Our Project (SMT Divergence Signals)

Our project requires:

1. **Standard indicators** (RSI, MACD, moving averages, Bollinger Bands, etc.) — All libraries cover this.
2. **Swing high/low detection** — **No library provides this out of the box.** Must be custom-built regardless of library choice.
3. **Divergence detection (SMT)** — SMT divergence compares price action between correlated assets (e.g., BTC vs ETH), not indicator divergence (e.g., RSI vs price). **No library supports this.** Must be custom-built.
4. **Multi-timeframe** — All libraries work with any timeframe OHLCV data; this is a data-fetching concern, not a TA library concern.
5. **Plugin architecture** — We need the TA library to compute raw indicators; the divergence/signal logic sits in our domain layer.

**Key insight:** Since SMT divergence detection (swing high/low comparison between correlated assets) must be custom-built regardless, the TA library choice comes down to: **indicator computation quality, performance, reliability, and ease of integration.**

---

## Recommendation

### Primary choice: **TA-Lib** (`ta-lib-python`)

**Rationale:**

1. **Industry standard with proven accuracy** — 20+ years of battle-tested algorithms. When building a signal system that traders rely on, indicator accuracy is non-negotiable.
2. **Best performance** — C-based vectorized computation is significantly faster than pure Python alternatives. This matters when scanning multiple assets across multiple timeframes.
3. **Largest indicator set** (200+) plus **unique candlestick pattern recognition** (60+ patterns) — provides maximum flexibility for future signal plugins.
4. **Actively maintained** — regular releases through 2025, binary wheels for easy installation, Pandas + Polars support.
5. **Installation is no longer a blocker** — binary wheels since v0.6.5 cover most platforms. Docker deployment (planned in Phase 10) eliminates remaining edge cases.

### Fallback / Complement: **pandas-ta-classic**

If TA-Lib installation proves problematic in a specific environment, `pandas-ta-classic` serves as a solid fallback:
- Pure Python, trivial to install
- Actively maintained fork (releases through Feb 2026)
- 200+ indicators, highly correlated with TA-Lib output
- Native Pandas extension for ergonomic DataFrame workflows

### For future real-time streaming: **talipp** (worth noting)

If the project evolves toward real-time tick-by-tick processing, talipp's O(1) incremental computation would be valuable. Not needed for the current candle-close-based signal checking design.

### Not recommended as primary:

- **ta (bukosabino)** — Unmaintained since Nov 2023, only 43 indicators, bugs unfixed. High download count is inertia, not a quality signal.
- **FinTA** — Self-described as inaccurate, LGPL license adds restrictions, limited community.
- **ta-py** — Has built-in divergence detection but too small/untested for production. Its divergence approach (indicator vs price) also differs from SMT divergence (price vs price across assets).

### Custom components we must build regardless:

No matter which library is chosen, the following must be implemented in our domain layer:
- **Swing high/low detection algorithm** (local extrema identification with configurable lookback)
- **SMT divergence logic** (comparing swing points between two correlated assets)
- **Signal scoring and filtering**

---

## Sources

- [TA-Lib Official Site](https://ta-lib.org/)
- [TA-Lib Python Wrapper GitHub](https://github.com/TA-Lib/ta-lib-python)
- [TA-Lib All Supported Indicators](https://ta-lib.github.io/ta-lib-python/funcs.html)
- [TA-Lib on PyPI](https://pypi.org/project/TA-Lib/)
- [TA-Lib Package Health (Snyk)](https://snyk.io/advisor/python/ta-lib)
- [pandas-ta on PyPI](https://pypi.org/project/pandas-ta/)
- [pandas-ta Official Site](https://www.pandas-ta.dev/)
- [pandas-ta-classic GitHub](https://github.com/xgboosted/pandas-ta-classic)
- [pandas-ta Package Health (Snyk)](https://snyk.io/advisor/python/pandas-ta)
- [ta (bukosabino) GitHub](https://github.com/bukosabino/ta)
- [ta on PyPI](https://pypi.org/project/ta/)
- [talipp GitHub](https://github.com/nardew/talipp)
- [talipp on PyPI](https://pypi.org/project/talipp/)
- [FinTA GitHub](https://github.com/peerchemist/finta)
- [FinTA on PyPI](https://pypi.org/project/finta/)
- [ta-py on PyPI](https://pypi.org/project/ta-py/)
- [stockstats on PyPI](https://pypi.org/project/stockstats/)
- [Comparing TA-Lib to pandas-ta — Sling Academy](https://www.slingacademy.com/article/comparing-ta-lib-to-pandas-ta-which-one-to-choose/)
- [Top Python Libraries for Algorithmic Trading 2025 — Analytics Insight](https://www.analyticsinsight.net/data-science/top-python-libraries-for-algorithmic-trading-and-finance-in-2025)
- [Top 4 Python Libraries for Technical Analysis — Medium](https://medium.com/geekculture/top-4-python-libraries-for-technical-analysis-db4f1ea87e09)
- [RSI Divergence in Python — Raposa Trade](https://raposa.trade/blog/test-and-trade-rsi-divergence-in-python/)
- [Enhancing Technical Analysis: Faster Alternative to TA-Lib — Medium](https://medium.com/@jpolec_72972/enhancing-technical-analysis-our-faster-alternative-to-ta-lib-f224d3db6b1e)
