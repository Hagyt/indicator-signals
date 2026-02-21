from services.coingecko_service import CoinGecko
from services.notification_service import Notification
from services.tradingview_service import TradingView
from services.smt_service import SMTDetector
from models.smt_signals import SMTPairConfig
from tradingview_ta import Interval
from utils.util import Utils
import time

cg = CoinGecko()

# ----- SMT Divergence pair configs -----
SMT_PAIRS = [
    SMTPairConfig(
        asset_a="BTCUSDT",
        asset_b="ETHUSDT",
        label_a="BTC",
        label_b="ETH",
        timeframes=["1h", "4h"],
    ),
    SMTPairConfig(
        asset_a="ETHUSDT",
        asset_b="SOLUSDT",
        label_a="ETH",
        label_b="SOL",
        timeframes=["1h", "4h"],
    ),
]


def scan_ta_signals():
    """Original TradingView oscillator + MA signal scan."""
    coins = cg.get_all_coins()
    for coin in coins:
        print(coin.symbol)

        try:
            icon_path = Utils.download_image(coin.image)
            analysis = TradingView.retrieve_analysis(
                (coin.symbol + "USDT").capitalize(), "Binance", Interval.INTERVAL_1_HOUR
            )

            if (
                analysis.oscillators["RECOMMENDATION"] == "NEUTRAL"
                and analysis.moving_averages["RECOMMENDATION"] == "NEUTRAL"
            ):
                Notification.send(
                    f"Buy signal for {coin.symbol.upper()}",
                    "Both Oscillators and Moving averages have generated a buy signal.",
                    icon_path,
                )

        except Exception as e:
            print(e)

        finally:
            time.sleep(1)
            Utils.delete_image(icon_path)


def scan_smt_divergences():
    """Scan configured pairs for SMT divergence signals."""
    for pair_cfg in SMT_PAIRS:
        label = f"{pair_cfg.label_a}/{pair_cfg.label_b}"
        print(f"SMT scan: {label}")

        try:
            detector = SMTDetector(pair_cfg)
            divergences = detector.scan()
            latest = SMTDetector.get_latest_divergence(divergences)

            if latest:
                direction = latest.direction.value.upper()
                Notification.send(
                    f"{direction} SMT divergence: {label}",
                    latest.description,
                    "",
                )

        except Exception as e:
            print(f"SMT scan error ({label}): {e}")


def main():
    scan_ta_signals()
    scan_smt_divergences()


if __name__ == "__main__":
    while True:
        main()
        time.sleep(300)
