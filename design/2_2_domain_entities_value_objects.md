# Design 2.2 — Domain Entities, Value Objects, and Aggregates

> **Task:** Define domain entities, value objects, and aggregates (Asset, Timeframe, Signal, Divergence, MarketData, etc.).

---

## DDD Building Blocks Refresher

| Concept | Identity? | Mutable? | Description |
|---------|-----------|----------|-------------|
| **Value Object** | No (equality by value) | Immutable | Describes a characteristic. Two VOs with same values are equal |
| **Entity** | Yes (equality by ID) | Mutable | Has a unique identity that persists over time |
| **Aggregate** | Entity that is a consistency boundary | Mutable | Cluster of entities/VOs treated as a unit. Has a root entity |

---

## Value Objects

### 1. `AssetSymbol`

Represents a tradable asset or index identifier.

```python
@dataclass(frozen=True)
class AssetSymbol:
    """A tradable asset or index symbol."""
    symbol: str          # e.g., "BTC/USDT", "ETH/USDT", "TOTAL", "TOTAL2"
    asset_type: AssetType  # CRYPTO_PAIR, INDEX, FOREX_PAIR, STOCK

    def base_currency(self) -> str:
        """Extract base currency. 'BTC/USDT' → 'BTC', 'TOTAL' → 'TOTAL'."""
        ...

    def quote_currency(self) -> str | None:
        """Extract quote currency. 'BTC/USDT' → 'USDT', 'TOTAL' → None."""
        ...
```

**Why Value Object:** An asset symbol is defined entirely by its value. Two `AssetSymbol("BTC/USDT", CRYPTO_PAIR)` are the same thing.

### 2. `AssetType` (Enum)

```python
class AssetType(str, Enum):
    CRYPTO_PAIR = "crypto_pair"    # BTC/USDT, ETH/USDT
    INDEX = "index"                # TOTAL, TOTAL2, TOTAL3
    FOREX_PAIR = "forex_pair"     # EUR/USD (future)
    STOCK = "stock"               # AAPL (future)
```

### 3. `Timeframe`

Represents a candle interval.

```python
@dataclass(frozen=True)
class Timeframe:
    """A candle interval."""
    value: str           # "1m", "5m", "15m", "1h", "4h", "1d", "1w"

    @property
    def minutes(self) -> int:
        """Duration in minutes. '4h' → 240, '1d' → 1440."""
        ...

    def __lt__(self, other: "Timeframe") -> bool:
        return self.minutes < other.minutes
```

**Predefined constants:**

```python
class Timeframes:
    M1  = Timeframe("1m")
    M5  = Timeframe("5m")
    M15 = Timeframe("15m")
    H1  = Timeframe("1h")
    H4  = Timeframe("4h")
    D1  = Timeframe("1d")
    W1  = Timeframe("1w")
```

### 4. `Candle` (OHLCV)

A single OHLCV data point.

```python
@dataclass(frozen=True)
class Candle:
    """A single OHLCV candle."""
    timestamp: datetime    # UTC candle open time
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open

    @property
    def body_size(self) -> Decimal:
        return abs(self.close - self.open)
```

**Why Value Object:** A candle is fully defined by its data. Same timestamp + same OHLCV = same candle.

### 5. `AssetPair`

Represents two correlated assets configured for comparison (e.g., for SMT divergence).

```python
@dataclass(frozen=True)
class AssetPair:
    """Two correlated assets for divergence comparison."""
    asset_a: AssetSymbol
    asset_b: AssetSymbol
    correlation: CorrelationType   # POSITIVE or NEGATIVE

    @property
    def label(self) -> str:
        return f"{self.asset_a.symbol} vs {self.asset_b.symbol}"
```

### 6. `CorrelationType` (Enum)

```python
class CorrelationType(str, Enum):
    POSITIVE = "positive"   # BTC & ETH move together
    NEGATIVE = "negative"   # DXY & EUR/USD move inversely
```

### 7. `SwingPoint`

A confirmed pivot (swing high or swing low) on price data.

```python
@dataclass(frozen=True)
class SwingPoint:
    """A confirmed swing high or swing low."""
    type: SwingType          # HIGH or LOW
    index: int               # Bar index in the OHLCV series
    timestamp: datetime      # UTC time of the pivot candle
    price: Decimal           # The high (for swing high) or low (for swing low)
    confirmation_index: int  # Bar index when the pivot was confirmed (index + right_lookback)
```

### 8. `SwingType` (Enum)

```python
class SwingType(str, Enum):
    HIGH = "high"
    LOW = "low"
```

### 9. `PairedSwing`

Two swing points (one from each asset) that correspond in time.

```python
@dataclass(frozen=True)
class PairedSwing:
    """A pair of corresponding swing points from two assets."""
    swing_a: SwingPoint       # Swing from asset A
    swing_b: SwingPoint       # Swing from asset B
    type: SwingType           # HIGH or LOW (both must match)
```

### 10. `DivergenceType` (Enum)

```python
class DivergenceType(str, Enum):
    BULLISH = "bullish"    # Potential bottom / reversal up
    BEARISH = "bearish"    # Potential top / reversal down
```

### 11. `SignalStrength` (Enum)

```python
class SignalStrength(str, Enum):
    WEAK = "weak"          # Single timeframe, no confluence
    MODERATE = "moderate"  # Single timeframe with confluence factors
    STRONG = "strong"      # Multi-timeframe confirmation
```

### 12. `InvalidationLevel`

The price level at which a signal becomes invalid.

```python
@dataclass(frozen=True)
class InvalidationLevel:
    """Price level that invalidates a signal."""
    price: Decimal
    asset: AssetSymbol
    description: str  # e.g., "Price above swing high at $105,200"
```

---

## Entities

### 1. `Signal`

The primary domain entity. Represents a detected trading signal with a unique identity and lifecycle.

```python
@dataclass
class Signal:
    """A detected trading signal."""
    id: SignalId                       # Unique identifier (UUID)
    strategy_name: str                 # e.g., "smt_divergence", "rsi_divergence"
    asset_pair: AssetPair              # The assets involved
    timeframe: Timeframe               # Timeframe of detection
    divergence_type: DivergenceType    # BULLISH or BEARISH
    strength: SignalStrength           # WEAK, MODERATE, STRONG
    detected_at: datetime              # UTC time of detection
    confirmation_at: datetime          # UTC time of confirmation (after right lookback)
    invalidation_level: InvalidationLevel
    status: SignalStatus               # ACTIVE, INVALIDATED, EXPIRED
    metadata: dict                     # Strategy-specific extra data

    # Lifecycle methods
    def invalidate(self, reason: str, at: datetime) -> None:
        """Mark this signal as invalidated."""
        self.status = SignalStatus.INVALIDATED
        self.invalidated_at = at
        self.invalidation_reason = reason

    def expire(self, at: datetime) -> None:
        """Mark this signal as expired (too old to be actionable)."""
        self.status = SignalStatus.EXPIRED
        self.expired_at = at

    @property
    def is_active(self) -> bool:
        return self.status == SignalStatus.ACTIVE
```

**Why Entity:** Each signal has a unique identity (UUID). Two signals detected at the same time for the same pair are still distinct signals. Signals have lifecycle state (active → invalidated/expired).

### 2. `SignalStatus` (Enum)

```python
class SignalStatus(str, Enum):
    ACTIVE = "active"             # Signal is live and actionable
    INVALIDATED = "invalidated"   # Price exceeded invalidation level
    EXPIRED = "expired"           # Signal aged out (configurable TTL)
```

### 3. `SignalId` (Value Object used as Entity ID)

```python
@dataclass(frozen=True)
class SignalId:
    value: UUID

    @staticmethod
    def generate() -> "SignalId":
        return SignalId(value=uuid4())
```

---

## Aggregates

### 1. `MarketDataSeries` (Aggregate Root)

A collection of candles for a specific asset and timeframe. This is the unit that strategies operate on.

```python
@dataclass
class MarketDataSeries:
    """Aggregate: a series of OHLCV candles for one asset/timeframe."""
    asset: AssetSymbol
    timeframe: Timeframe
    candles: list[Candle]            # Sorted by timestamp ascending
    last_updated: datetime

    @property
    def highs(self) -> np.ndarray:
        """NumPy array of high prices for indicator/pivot computation."""
        return np.array([c.high for c in self.candles], dtype=float)

    @property
    def lows(self) -> np.ndarray:
        return np.array([c.low for c in self.candles], dtype=float)

    @property
    def closes(self) -> np.ndarray:
        return np.array([c.close for c in self.candles], dtype=float)

    @property
    def volumes(self) -> np.ndarray:
        return np.array([c.volume for c in self.candles], dtype=float)

    @property
    def timestamps(self) -> list[datetime]:
        return [c.timestamp for c in self.candles]

    @property
    def latest_candle(self) -> Candle | None:
        return self.candles[-1] if self.candles else None

    def slice(self, since: datetime, until: datetime) -> "MarketDataSeries":
        """Return a sub-series within the given time range."""
        ...

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for TA library compatibility."""
        ...
```

**Why Aggregate:** The series is the consistency boundary — you never operate on a single candle in isolation. Strategies always receive a full series. The series enforces invariants like sorted order and time alignment.

**Invariants:**
- Candles are always sorted by timestamp ascending
- No duplicate timestamps
- All candles belong to the same asset and timeframe

---

### 2. `Divergence` (Aggregate Root)

Represents a detected divergence between two assets, including the swing points that formed it.

```python
@dataclass
class Divergence:
    """Aggregate: a detected divergence between two correlated assets."""
    id: UUID
    type: DivergenceType                # BULLISH or BEARISH
    asset_pair: AssetPair               # The two assets compared
    timeframe: Timeframe

    # The two consecutive paired swings that formed the divergence
    previous_swing: PairedSwing         # First paired swing point
    current_swing: PairedSwing          # Second paired swing point (divergent)

    # Derived from swing points
    asset_a_direction: str              # "higher_high", "lower_low", "higher_low", "lower_high"
    asset_b_direction: str              # "higher_high", "lower_low", "higher_low", "lower_high"

    detected_at: datetime
    invalidation_level: InvalidationLevel

    @property
    def description(self) -> str:
        """Human-readable divergence description."""
        return (
            f"{self.type.value.title()} SMT Divergence: "
            f"{self.asset_pair.asset_a.symbol} {self.asset_a_direction} "
            f"vs {self.asset_pair.asset_b.symbol} {self.asset_b_direction} "
            f"on {self.timeframe.value}"
        )
```

**Why Aggregate:** A divergence is a composite concept — it only exists as a combination of paired swing points, asset pair context, and type classification. The divergence enforces the invariant that the swing point comparison is valid.

**Invariants:**
- `previous_swing` and `current_swing` must be the same `SwingType` (both HIGH or both LOW)
- The swing directions must actually diverge (asset A goes one way, asset B goes the other)
- Both swings must be from the same asset pair and timeframe

---

### 3. `ScanResult` (Aggregate Root)

Represents the result of running a strategy scan — groups all signals found in a single scan execution.

```python
@dataclass
class ScanResult:
    """Aggregate: the result of a single strategy scan execution."""
    id: UUID
    strategy_name: str
    asset_pair: AssetPair
    timeframe: Timeframe
    executed_at: datetime
    signals: list[Signal]               # Signals detected in this scan
    candles_analyzed: int               # How many candles were analyzed
    scan_duration_ms: int               # Performance tracking

    @property
    def has_signals(self) -> bool:
        return len(self.signals) > 0

    @property
    def signal_count(self) -> int:
        return len(self.signals)
```

**Why Aggregate:** Groups signals from a single scan execution. Useful for deduplication (compare new scan results against previous ones), audit logging, and performance monitoring.

---

## Domain Model Diagram

```
                          VALUE OBJECTS
                    ┌──────────────────────┐
                    │  AssetSymbol         │
                    │  AssetType (enum)    │
                    │  Timeframe           │
                    │  Candle              │
                    │  AssetPair           │
                    │  CorrelationType     │
                    │  SwingPoint          │
                    │  SwingType (enum)    │
                    │  PairedSwing         │
                    │  DivergenceType      │
                    │  SignalStrength      │
                    │  InvalidationLevel   │
                    │  SignalId            │
                    │  SignalStatus (enum) │
                    └──────────────────────┘

                           ENTITIES
                    ┌──────────────────────┐
                    │  Signal              │──── has lifecycle (active/invalidated/expired)
                    └──────────────────────┘

                         AGGREGATES
    ┌───────────────────┐  ┌──────────────┐  ┌─────────────┐
    │  MarketDataSeries │  │  Divergence  │  │  ScanResult │
    │  (root)           │  │  (root)      │  │  (root)     │
    │                   │  │              │  │             │
    │  ◆ list[Candle]   │  │  ◆ PairedSw  │  │  ◆ list[Sig]│
    └───────────────────┘  │  ◆ PairedSw  │  └─────────────┘
                           │  ◆ AssetPair │
                           │  ◆ Timeframe │
                           └──────────────┘
```

---

## Relationships

```
AssetPair ◆──── AssetSymbol (asset_a)
          ◆──── AssetSymbol (asset_b)
          ◆──── CorrelationType

MarketDataSeries ◆──── AssetSymbol
                 ◆──── Timeframe
                 ◆──── list[Candle]

SwingPoint ──── uses Candle data (high/low price + timestamp)

PairedSwing ◆──── SwingPoint (swing_a)
            ◆──── SwingPoint (swing_b)

Divergence ◆──── PairedSwing (previous_swing)
           ◆──── PairedSwing (current_swing)
           ◆──── AssetPair
           ◆──── Timeframe
           ◆──── InvalidationLevel

Signal ◆──── AssetPair
       ◆──── Timeframe
       ◆──── DivergenceType
       ◆──── SignalStrength
       ◆──── InvalidationLevel
       ◆──── SignalStatus

ScanResult ◆──── list[Signal]
           ◆──── AssetPair
           ◆──── Timeframe
```

---

## Usage Examples

### Creating a Market Data Series

```python
series = MarketDataSeries(
    asset=AssetSymbol("BTC/USDT", AssetType.CRYPTO_PAIR),
    timeframe=Timeframes.H4,
    candles=[
        Candle(timestamp=dt(2026, 3, 14, 0), open=D("104500"), high=D("105200"), low=D("104100"), close=D("104800"), volume=D("1200")),
        Candle(timestamp=dt(2026, 3, 14, 4), open=D("104800"), high=D("105500"), low=D("104600"), close=D("105100"), volume=D("980")),
        # ...
    ],
    last_updated=datetime.utcnow(),
)
```

### Creating a Signal

```python
signal = Signal(
    id=SignalId.generate(),
    strategy_name="smt_divergence",
    asset_pair=AssetPair(
        asset_a=AssetSymbol("BTC/USDT", AssetType.CRYPTO_PAIR),
        asset_b=AssetSymbol("ETH/USDT", AssetType.CRYPTO_PAIR),
        correlation=CorrelationType.POSITIVE,
    ),
    timeframe=Timeframes.H4,
    divergence_type=DivergenceType.BEARISH,
    strength=SignalStrength.MODERATE,
    detected_at=datetime.utcnow(),
    confirmation_at=datetime.utcnow(),
    invalidation_level=InvalidationLevel(
        price=Decimal("105500"),
        asset=AssetSymbol("BTC/USDT", AssetType.CRYPTO_PAIR),
        description="Price above swing high at $105,500",
    ),
    status=SignalStatus.ACTIVE,
    metadata={"divergence_id": str(divergence.id)},
)
```

### Invalidating a Signal

```python
if current_candle.high > signal.invalidation_level.price:
    signal.invalidate(
        reason="Price exceeded invalidation level",
        at=current_candle.timestamp,
    )
```

---

## Design Decisions

### 1. `Decimal` vs `float` for prices
- **Decision:** Use `Decimal` in domain objects for accuracy, convert to `float`/`np.ndarray` at the boundary when feeding into TA libraries (NumPy, pandas-ta).
- **Rationale:** Financial data should not suffer floating-point imprecision in the domain layer. The conversion to float is explicit and happens only when interfacing with numerical computation libraries.

### 2. Frozen dataclasses for Value Objects
- **Decision:** All value objects use `@dataclass(frozen=True)`.
- **Rationale:** Immutability ensures value objects can be safely shared, used as dict keys, and stored in sets.

### 3. Separate `Divergence` from `Signal`
- **Decision:** `Divergence` is its own aggregate; `Signal` references it via metadata.
- **Rationale:** A divergence is a structural market observation. A signal is an actionable alert derived from one or more observations. Different strategies may produce signals from different types of analysis (divergence, indicator crossover, pattern recognition) — keeping `Signal` generic allows the plugin system to work uniformly.

### 4. `MarketDataSeries` provides NumPy arrays
- **Decision:** The aggregate exposes `.highs`, `.lows`, `.closes` as `np.ndarray` properties.
- **Rationale:** TA libraries (TA-Lib, pandas-ta) operate on NumPy arrays. Providing these as computed properties keeps the domain model clean while enabling efficient computation at the boundary.

### 5. `ScanResult` for deduplication
- **Decision:** Each scan produces a `ScanResult` aggregate that can be compared against previous results.
- **Rationale:** Signal deduplication (Phase 6.3) needs to compare "what was found this scan" vs "what was already emitted." The `ScanResult` provides that comparison boundary.
