# Research 1.4 — SMT Divergence Calculation

> **Task:** Research SMT (Smart Money Technique) divergence calculation: definition, required data, detection algorithm between correlated assets.

---

## What is SMT Divergence?

**SMT Divergence (Smart Money Technique Divergence)** is a price action analysis method from the ICT (Inner Circle Trader) methodology, developed by Michael J. Huddleston. It identifies moments when two correlated assets that normally move in sync **diverge in their swing structure** — one makes a new swing high/low while the other fails to do so.

This divergence between correlated assets is interpreted as a sign that **institutional ("smart money") players are positioning for a reversal**, using one asset's move to distribute or accumulate in the other.

**Key distinction from traditional divergence:** SMT divergence compares **price vs price** across two correlated assets. It does NOT compare price vs indicator (like RSI divergence). It is purely a price action concept.

---

## Types of SMT Divergence

### Bearish SMT Divergence (Potential Top / Reversal Down)

For **positively correlated** assets (e.g., BTC and ETH):

```
Asset A (BTC):  ... → Swing High → ... → Higher High (HH)  ← makes new high
Asset B (ETH):  ... → Swing High → ... → Lower High (LH)   ← fails to follow

Signal: Bearish — uptrend is weakening, Smart Money may be distributing.
```

- Asset A makes a **Higher High** while Asset B makes a **Lower High**
- Indicates buying momentum is not genuine across both assets
- Smart Money is likely using Asset A's new high to sell (distribute) Asset B

### Bullish SMT Divergence (Potential Bottom / Reversal Up)

For **positively correlated** assets:

```
Asset A (BTC):  ... → Swing Low → ... → Lower Low (LL)   ← makes new low
Asset B (ETH):  ... → Swing Low → ... → Higher Low (HL)   ← fails to follow

Signal: Bullish — downtrend is weakening, Smart Money may be accumulating.
```

- Asset A makes a **Lower Low** while Asset B makes a **Higher Low**
- Indicates selling pressure is not genuine across both assets
- Smart Money is likely using Asset A's new low to buy (accumulate) Asset B

### For Negatively Correlated Assets (e.g., DXY vs EUR/USD)

The logic inverts: if DXY makes a Higher High, EUR/USD is expected to make a Lower Low. If EUR/USD fails to make a new Lower Low, that's an SMT divergence.

---

## Required Data

### 1. OHLCV Data for Both Assets

| Requirement | Detail |
|-------------|--------|
| Data type | OHLCV candles (Open, High, Low, Close, Volume) |
| Assets | Two correlated assets on the same timeframe |
| Alignment | Candles must be **time-aligned** (same timestamps) |
| History needed | Enough bars to detect at least 2 consecutive swing points per asset |
| Minimum bars | Depends on pivot lookback, but typically 50–200+ candles |

### 2. Configurable Asset Pairs

Common pairs for SMT analysis:

| Market | Asset A | Asset B | Correlation |
|--------|---------|---------|-------------|
| Crypto | BTC/USDT | ETH/USDT | ~0.89 (positive) |
| Crypto | BTC/USDT | TOTAL (market cap) | Positive |
| Crypto | BTC/USDT | TOTAL2 (excl. BTC) | Positive |
| Crypto | BTC/USDT | TOTAL3 (excl. BTC+ETH) | Positive |
| Forex | EUR/USD | GBP/USD | Positive |
| Forex | DXY | EUR/USD | Negative (inverse) |
| Indices | ES (S&P 500) | NQ (Nasdaq 100) | Positive |
| Commodities | Gold (XAU) | Silver (XAG) | Positive |

### 3. Configuration Parameters

| Parameter | Description | Typical Values |
|-----------|-------------|----------------|
| `pivot_lookback_left` | Bars to the left a swing point must exceed | 3–10 |
| `pivot_lookback_right` | Bars to the right for confirmation | 3–10 |
| `correlation_type` | Positive or negative correlation | `positive` / `negative` |
| `timeframe` | Candle interval | 5m, 15m, 1H, 4H, 1D |
| `max_swing_distance` | Max bars between compared swing points on both assets | 5–20 |

---

## Detection Algorithm

### Step 1: Swing Point Detection (Pivot High/Low)

A **Swing High** is a candle whose `high` is higher than the `high` of N candles on both its left and right sides. A **Swing Low** is a candle whose `low` is lower than the `low` of N candles on both sides.

```
Swing High at bar[i]:
    high[i] > high[i-1], high[i-2], ..., high[i-L]   (left lookback)
    AND
    high[i] > high[i+1], high[i+2], ..., high[i+R]   (right lookback — confirmation delay)

Swing Low at bar[i]:
    low[i] < low[i-1], low[i-2], ..., low[i-L]
    AND
    low[i] < low[i+1], low[i+2], ..., low[i+R]
```

**Important:** The right lookback introduces a **confirmation delay** of R bars. A swing high at bar `i` is only confirmed at bar `i + R`. This prevents repainting but means signals are delayed.

#### Python implementation approach:

```python
from scipy.signal import argrelextrema
import numpy as np

def detect_swing_highs(highs: np.ndarray, order: int = 5) -> np.ndarray:
    """Returns indices of swing highs."""
    return argrelextrema(highs, np.greater, order=order)[0]

def detect_swing_lows(lows: np.ndarray, order: int = 5) -> np.ndarray:
    """Returns indices of swing lows."""
    return argrelextrema(lows, np.less, order=order)[0]
```

Alternative: manual pivot detection loop (more control over left/right lookback independently):

```python
def detect_pivots(data: np.ndarray, left: int, right: int, comparator) -> list[int]:
    """Detect pivot points with asymmetric left/right lookback."""
    pivots = []
    for i in range(left, len(data) - right):
        is_pivot = True
        for j in range(1, left + 1):
            if not comparator(data[i], data[i - j]):
                is_pivot = False
                break
        if is_pivot:
            for j in range(1, right + 1):
                if not comparator(data[i], data[i + j]):
                    is_pivot = False
                    break
        if is_pivot:
            pivots.append(i)
    return pivots
```

#### Pivot strength settings:

| Setting | Effect | Use Case |
|---------|--------|----------|
| Low (2-3 left/right) | More pivots, catches minor swings | Lower timeframes (5m, 15m) |
| Medium (5 left/right) | Balanced — structural pivots | Standard analysis (1H, 4H) |
| High (8-10 left/right) | Fewer pivots, only major swings | Higher timeframes (1D, 1W) |

### Step 2: Time-Align Swing Points Between Assets

After detecting swing points independently on each asset, we need to find **corresponding** swing points — swings that occur at approximately the same time on both assets.

```
For each swing high on Asset A:
    Find the nearest swing high on Asset B within ±max_swing_distance bars
    If found → this is a "paired" swing high for comparison

For each swing low on Asset A:
    Find the nearest swing low on Asset B within ±max_swing_distance bars
    If found → this is a "paired" swing low for comparison
```

### Step 3: Compare Consecutive Paired Swing Points

For **bearish SMT** (comparing swing highs):
```
Given two consecutive paired swing highs (pair1, pair2):

Asset A: swing_high_1 → swing_high_2
Asset B: swing_high_1 → swing_high_2

IF (for positive correlation):
    Asset_A.swing_high_2 > Asset_A.swing_high_1   (Higher High on A)
    AND
    Asset_B.swing_high_2 < Asset_B.swing_high_1   (Lower High on B)
THEN:
    → Bearish SMT Divergence detected
```

For **bullish SMT** (comparing swing lows):
```
Given two consecutive paired swing lows (pair1, pair2):

IF (for positive correlation):
    Asset_A.swing_low_2 < Asset_A.swing_low_1   (Lower Low on A)
    AND
    Asset_B.swing_low_2 > Asset_B.swing_low_1   (Higher Low on B)
THEN:
    → Bullish SMT Divergence detected
```

For **negative correlation**, the logic flips: both assets are expected to move in opposite directions, so the divergence is when they move in the same direction.

### Step 4: Signal Invalidation

A detected SMT divergence is invalidated when:

- **Bearish SMT invalidated:** Price trades **above** the high of the confirmation pivot (the swing high that formed the divergence)
- **Bullish SMT invalidated:** Price trades **below** the low of the confirmation pivot (the swing low that formed the divergence)

```python
def is_invalidated(divergence, current_candle):
    if divergence.type == 'bearish':
        # Invalidated if price exceeds the swing high that formed the divergence
        return current_candle.high > divergence.confirmation_pivot_high
    elif divergence.type == 'bullish':
        # Invalidated if price drops below the swing low that formed the divergence
        return current_candle.low < divergence.confirmation_pivot_low
```

### Step 5: Optional — Candle Direction Validation

An additional filter used by some implementations:

- For **bullish SMT**: the swing low candle on both assets should be a **down candle** (close < open) — confirming selling exhaustion
- For **bearish SMT**: the swing high candle on both assets should be an **up candle** (close > open) — confirming buying exhaustion

This filter eliminates low-probability SMT setups that are more frequently broken.

---

## Complete Algorithm Pseudocode

```
FUNCTION detect_smt_divergences(asset_a_ohlcv, asset_b_ohlcv, config):

    # Step 1: Detect swing points
    a_swing_highs = detect_pivots(asset_a.high, config.left, config.right, ">")
    a_swing_lows  = detect_pivots(asset_a.low,  config.left, config.right, "<")
    b_swing_highs = detect_pivots(asset_b.high, config.left, config.right, ">")
    b_swing_lows  = detect_pivots(asset_b.low,  config.left, config.right, "<")

    # Step 2: Pair corresponding swing points by time proximity
    paired_highs = pair_swings(a_swing_highs, b_swing_highs, config.max_distance)
    paired_lows  = pair_swings(a_swing_lows,  b_swing_lows,  config.max_distance)

    divergences = []

    # Step 3: Check consecutive paired highs for bearish SMT
    FOR i FROM 1 TO len(paired_highs):
        prev = paired_highs[i-1]
        curr = paired_highs[i]

        IF config.correlation == POSITIVE:
            a_higher_high = curr.a_price > prev.a_price
            b_lower_high  = curr.b_price < prev.b_price

            IF a_higher_high AND b_lower_high:
                divergences.append(BearishSMT(curr))
            ELIF (not a_higher_high) AND (not b_lower_high):
                # Also check: A makes lower high, B makes higher high
                divergences.append(BearishSMT(curr))

    # Step 4: Check consecutive paired lows for bullish SMT
    FOR i FROM 1 TO len(paired_lows):
        prev = paired_lows[i-1]
        curr = paired_lows[i]

        IF config.correlation == POSITIVE:
            a_lower_low  = curr.a_price < prev.a_price
            b_higher_low = curr.b_price > prev.b_price

            IF a_lower_low AND b_higher_low:
                divergences.append(BullishSMT(curr))
            ELIF (not a_lower_low) AND (not b_higher_low):
                divergences.append(BullishSMT(curr))

    # Step 5: Optional candle direction filter
    IF config.candle_direction_filter:
        divergences = filter_by_candle_direction(divergences)

    RETURN divergences
```

---

## Multi-Timeframe Considerations

| Timeframe | Signal Strength | Use Case |
|-----------|----------------|----------|
| 1D, 1W | Highest reliability | Macro bias / swing trading |
| 4H | Strong | Intraday bias setting |
| 1H | Moderate | Entry timing with HTF confluence |
| 15m, 5m | Lower reliability alone | Precise entry within HTF signal |

**Best practice per ICT methodology:**
1. Identify SMT divergence on **higher timeframe** (4H, 1D) for directional bias
2. Drop to **lower timeframe** (15m, 5m) for entry timing
3. SMT on multiple timeframes simultaneously = strongest signal

---

## Key Implementation Decisions for Our Project

### 1. Swing Detection Method

| Option | Pros | Cons |
|--------|------|------|
| `scipy.argrelextrema` | Simple, fast, NumPy native | Symmetric lookback only |
| Custom pivot loop | Asymmetric left/right, full control | More code to maintain |
| Rolling window min/max | Very fast | Less precise for true pivots |

**Recommendation:** Custom pivot loop — gives us independent control over left and right lookback, which is important because the right lookback determines confirmation delay.

### 2. Swing Pairing Strategy

| Option | Pros | Cons |
|--------|------|------|
| Nearest-in-time match | Simple, intuitive | May pair unrelated swings |
| Same-bar-index match | Strict alignment | Too rigid, misses valid pairs |
| Within-window match | Configurable tolerance | Needs `max_distance` tuning |

**Recommendation:** Within-window match with configurable `max_swing_distance` — allows for the natural slight timing differences between correlated assets while preventing false pairings.

### 3. Signal Output

Each detected SMT divergence should include:
- **Type:** Bullish or Bearish
- **Asset pair:** e.g., BTC/USDT vs ETH/USDT
- **Timeframe:** e.g., 4H
- **Swing points:** The two consecutive paired swings that formed the divergence (timestamps + prices on both assets)
- **Confirmation bar:** The bar at which the divergence was confirmed (swing point + right lookback)
- **Invalidation level:** The price level that would invalidate the divergence
- **Status:** Active / Invalidated

---

## Reference Implementations (Open Source)

### TradingView Pine Script (for logic reference, not direct use):

1. **SMT Divergences [LuxAlgo]** — [View Source](https://www.tradingview.com/script/ecEI56ff-SMT-Divergences-LuxAlgo/)
   - Detects swing points using pivot logic on both chart and external tickers
   - Uses configurable left/right lookback (default 3 bars)
   - Compares swing points at the same confirmation time

2. **SMT Divergences [OutOfOptions]** — [View Source](https://www.tradingview.com/script/WMgV6HcH-SMT-Divergences-OutOfOptions/)
   - Adds candle direction validation filter
   - Configurable pivot strength (bars left/right for pivot validity)
   - Open source with detailed comments

3. **SMT Time Windows** — [View](https://www.tradingview.com/script/AxON7Y50-SMT-Time-Windows/)
   - ICT-style SMT with session/time window filtering
   - Bullish: one symbol higher low, other lower low
   - Bearish: one symbol higher high, other lower high

### Python Libraries (for swing detection):

1. **scipy.signal.argrelextrema** — standard for local extrema detection
2. **sheevv/find-swing-highs-swing-lows** — [GitHub](https://github.com/sheevv/find-swing-highs-swing-lows) — dedicated Python swing detection
3. **Raposa Trade tutorial** — [Higher Highs/Lower Lows in Python](https://raposa.trade/blog/higher-highs-lower-lows-and-calculating-price-trends-in-python/)

---

## Sources

- [ICT SMT Divergence — Comprehensive Guide (InnerCircleTrader.net)](https://innercircletrader.net/tutorials/ict-smt-divergence-smart-money-technique/)
- [SMT Divergence in Trading: The Ultimate Guide (2026) — XS](https://www.xs.com/en/blog/smt-divergence/)
- [SMT Divergence — How to Trade Correlated Markets (FXOpen)](https://fxopen.com/blog/en/what-is-smt-divergence-and-how-can-you-use-it-in-trading/)
- [Bitcoin–Ethereum SMT Divergence — Bitsgap](https://bitsgap.com/blog/bitcoin-ethereum-smt-divergence-what-is-it-how-to-use-it)
- [Bitcoin–Ethereum SMT Divergence — Cryptohopper](https://www.cryptohopper.com/blog/bitcoin-ethereum-smt-divergence-one-is-stronger-one-is-weaker-5714)
- [Mastering SMT Divergence — Cryptohopper](https://www.cryptohopper.com/blog/mastering-smt-divergence-in-trading-11187)
- [How to Identify and Use SMT Divergence — FundYourFX](https://fundyourfx.com/mastering-smt-divergence-in-trading/)
- [ICT SMT Divergence — Dominate Forex (SmartMoneyICT)](https://smartmoneyict.com/ict-smt-divergence/)
- [SMT Divergence in ICT — TradingFinder](https://tradingfinder.com/education/forex/ict-smt-divergence/)
- [SMT Divergence — PineScript Market](https://pinescriptmarket.com/learn/price-action/smt-divergence)
- [ICT SMT Divergence Guide — Forex Factory](https://www.forexfactory.com/thread/1342743-ict-smt-divergence-a-comprehensive-guide-tflab)
- [Smart Money Technique Divergences — Ultimate Guide (TradingView)](https://www.tradingview.com/chart/EURUSD/ITGLE2Qf-Smart-Money-Technique-SMT-Divergences-The-Ultimate-Guide/)
- [SMT Divergences [LuxAlgo] — TradingView](https://www.tradingview.com/script/ecEI56ff-SMT-Divergences-LuxAlgo/)
- [SMT Divergences [OutOfOptions] — TradingView](https://www.tradingview.com/script/WMgV6HcH-SMT-Divergences-OutOfOptions/)
- [SMT Time Windows — TradingView](https://www.tradingview.com/script/AxON7Y50-SMT-Time-Windows/)
- [Multi-Timeframe SFP + SMT — TradingView](https://www.tradingview.com/script/2sA2GYSi-Multi-Timeframe-SFP-SMT/)
- [Swing Suite (SMT/Divergences + Gann Swings) — TradingView](https://www.tradingview.com/script/FzgljscG-Swing-Suite-SMT-Divergences-Gann-Swings/)
- [Pivot-based Swing Highs and Lows — TradingView](https://www.tradingview.com/script/ffRnXR2F-Pivot-based-Swing-Highs-and-Lows/)
- [Swing Highs and Lows: Basics — LuxAlgo](https://www.luxalgo.com/blog/swing-highs-and-lows-basics-for-traders/)
- [Higher Highs, Lower Lows in Python — Raposa Trade](https://raposa.trade/blog/higher-highs-lower-lows-and-calculating-price-trends-in-python/)
- [Finding Local Extrema in Crypto/Stocks/Forex — Medium](https://medium.com/@marszyprow/finding-local-extrema-in-crypto-stocks-and-forex-using-python-ebfe0216b92d)
- [Swing High/Low Detection — GitHub (sheevv)](https://github.com/sheevv/find-swing-highs-swing-lows)
- [Finding HH, LL, LH, HL with Python — MadraDavid](https://madradavid.com/finding-higher-highs-lower-lows-lower-highs-and-higher-lows-python/)
- [SMT (Smart Money Technique) Guide — Phemex](https://phemex.com/academy/what-is-smt-smart-money-technique-guide-futures-trading)
- [Decoding SMT Divergence — OpoFinance](https://blog.opofinance.com/en/decoding-smt-divergence/)
- [Mastering Divergence Trading by ICT & SMT — Atmexx](https://www.atmexx.com/educational-articles/mastering-divergence-trading-ict-smt-strategies-explained)
