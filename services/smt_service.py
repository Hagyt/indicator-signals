from typing import List, Tuple, Dict, Optional
from models.smt_signals import SwingPoint, SMTDivergence, SMTDirection, SMTPairConfig
from services.binance_service import Binance


class SMTDetector:
    """Detects Smart Money Technique (SMT) divergence between correlated crypto pairs."""

    def __init__(self, config: SMTPairConfig):
        self.config = config

    # ------------------------------------------------------------------
    # Step 1: Swing point detection
    # ------------------------------------------------------------------

    @staticmethod
    def detect_swing_highs(
        candles: List[Dict], left: int, right: int
    ) -> List[SwingPoint]:
        """Find swing highs where the high is the max in a [left, right] window."""
        swings = []
        highs = [c["high"] for c in candles]

        for i in range(left, len(highs) - right):
            window = highs[i - left : i + right + 1]
            if highs[i] == max(window):
                # Only count if it's the unique max or the first occurrence
                if window.count(highs[i]) == 1 or window.index(highs[i]) == left:
                    swings.append(
                        SwingPoint(
                            timestamp=candles[i]["open_time"],
                            price=highs[i],
                            bar_index=i,
                            swing_type="high",
                        )
                    )
        return swings

    @staticmethod
    def detect_swing_lows(
        candles: List[Dict], left: int, right: int
    ) -> List[SwingPoint]:
        """Find swing lows where the low is the min in a [left, right] window."""
        swings = []
        lows = [c["low"] for c in candles]

        for i in range(left, len(lows) - right):
            window = lows[i - left : i + right + 1]
            if lows[i] == min(window):
                if window.count(lows[i]) == 1 or window.index(lows[i]) == left:
                    swings.append(
                        SwingPoint(
                            timestamp=candles[i]["open_time"],
                            price=lows[i],
                            bar_index=i,
                            swing_type="low",
                        )
                    )
        return swings

    # ------------------------------------------------------------------
    # Step 2: Match swing points between two assets
    # ------------------------------------------------------------------

    @staticmethod
    def match_swings(
        swings_a: List[SwingPoint],
        swings_b: List[SwingPoint],
        max_offset: int,
    ) -> List[Tuple[SwingPoint, SwingPoint]]:
        """
        Pair swing points between two assets that occur within max_offset bars
        of each other.  Each swing in B is used at most once.
        """
        matches = []
        used_b = set()

        for sa in swings_a:
            best_idx: Optional[int] = None
            best_dist = max_offset + 1

            for idx_b, sb in enumerate(swings_b):
                if idx_b in used_b:
                    continue
                dist = abs(sa.bar_index - sb.bar_index)
                if dist <= max_offset and dist < best_dist:
                    best_idx = idx_b
                    best_dist = dist

            if best_idx is not None:
                matches.append((sa, swings_b[best_idx]))
                used_b.add(best_idx)

        # Sort chronologically
        matches.sort(key=lambda pair: max(pair[0].bar_index, pair[1].bar_index))
        return matches

    # ------------------------------------------------------------------
    # Step 3: Detect divergence from consecutive matched swing pairs
    # ------------------------------------------------------------------

    @staticmethod
    def find_divergences(
        matched_highs: List[Tuple[SwingPoint, SwingPoint]],
        matched_lows: List[Tuple[SwingPoint, SwingPoint]],
        asset_a_label: str,
        asset_b_label: str,
        timeframe: str,
    ) -> List[SMTDivergence]:
        divergences: List[SMTDivergence] = []

        # Bearish SMT — consecutive swing highs diverge
        for i in range(1, len(matched_highs)):
            prev_a, prev_b = matched_highs[i - 1]
            curr_a, curr_b = matched_highs[i]

            a_hh = curr_a.price > prev_a.price
            b_lh = curr_b.price < prev_b.price
            a_lh = curr_a.price < prev_a.price
            b_hh = curr_b.price > prev_b.price

            if (a_hh and b_lh) or (a_lh and b_hh):
                divergences.append(
                    SMTDivergence(
                        direction=SMTDirection.BEARISH,
                        timestamp=max(curr_a.timestamp, curr_b.timestamp),
                        asset_a_symbol=asset_a_label,
                        asset_b_symbol=asset_b_label,
                        asset_a_prev_price=prev_a.price,
                        asset_a_curr_price=curr_a.price,
                        asset_b_prev_price=prev_b.price,
                        asset_b_curr_price=curr_b.price,
                        swing_type="high",
                        timeframe=timeframe,
                    )
                )

        # Bullish SMT — consecutive swing lows diverge
        for i in range(1, len(matched_lows)):
            prev_a, prev_b = matched_lows[i - 1]
            curr_a, curr_b = matched_lows[i]

            a_ll = curr_a.price < prev_a.price
            b_hl = curr_b.price > prev_b.price
            a_hl = curr_a.price > prev_a.price
            b_ll = curr_b.price < prev_b.price

            if (a_ll and b_hl) or (a_hl and b_ll):
                divergences.append(
                    SMTDivergence(
                        direction=SMTDirection.BULLISH,
                        timestamp=max(curr_a.timestamp, curr_b.timestamp),
                        asset_a_symbol=asset_a_label,
                        asset_b_symbol=asset_b_label,
                        asset_a_prev_price=prev_a.price,
                        asset_a_curr_price=curr_a.price,
                        asset_b_prev_price=prev_b.price,
                        asset_b_curr_price=curr_b.price,
                        swing_type="low",
                        timeframe=timeframe,
                    )
                )

        return divergences

    # ------------------------------------------------------------------
    # Public API: scan a pair for divergences
    # ------------------------------------------------------------------

    def scan(self, candle_limit: int = 100) -> List[SMTDivergence]:
        """
        Fetch candle data for both assets across all configured timeframes
        and return any detected SMT divergences.
        """
        all_divergences: List[SMTDivergence] = []

        for tf in self.config.timeframes:
            try:
                candles_a = Binance.get_klines(
                    self.config.asset_a, tf, limit=candle_limit
                )
                candles_b = Binance.get_klines(
                    self.config.asset_b, tf, limit=candle_limit
                )
            except Exception as e:
                print(f"Failed to fetch klines for {self.config.label_a}/{self.config.label_b} {tf}: {e}")
                continue

            if not candles_a or not candles_b:
                continue

            highs_a = self.detect_swing_highs(
                candles_a, self.config.swing_left, self.config.swing_right
            )
            highs_b = self.detect_swing_highs(
                candles_b, self.config.swing_left, self.config.swing_right
            )
            lows_a = self.detect_swing_lows(
                candles_a, self.config.swing_left, self.config.swing_right
            )
            lows_b = self.detect_swing_lows(
                candles_b, self.config.swing_left, self.config.swing_right
            )

            matched_highs = self.match_swings(
                highs_a, highs_b, self.config.max_offset_bars
            )
            matched_lows = self.match_swings(
                lows_a, lows_b, self.config.max_offset_bars
            )

            divergences = self.find_divergences(
                matched_highs,
                matched_lows,
                self.config.label_a,
                self.config.label_b,
                tf,
            )
            all_divergences.extend(divergences)

        return all_divergences

    @staticmethod
    def get_latest_divergence(
        divergences: List[SMTDivergence],
    ) -> Optional[SMTDivergence]:
        """Return the most recent divergence, or None."""
        if not divergences:
            return None
        return max(divergences, key=lambda d: d.timestamp)
