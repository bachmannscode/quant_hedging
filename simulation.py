from collections import defaultdict

import ccxt
import pandas as pd

from config_and_constants import (
    CLOSE,
    DATA_INTERVAL,
    DOLLAR_GAMMA,
    END,
    PRICE,
    QUANTITY,
    START,
    THRESHOLDS,
    TIMESTAMP,
    TRADING_PAIR,
)
from util import compute_all_pnls
from visualize import plot, export_table


def fetch_binance_data(
    symbol=TRADING_PAIR,
    timeframe=DATA_INTERVAL,
    start=START,
    end=END,
):
    exchange = ccxt.binance()
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    data = []
    since = start_ms
    while since < end_ms:
        candles = exchange.fetch_ohlcv(
            symbol,
            timeframe,
            since=since,
            params={"until": end_ms},
        )
        data.extend((candle[0], candle[4]) for candle in candles)
        since = candles[-1][0] + 1

    df = pd.DataFrame(data, columns=[TIMESTAMP, CLOSE])
    df[TIMESTAMP] = pd.to_datetime(df[TIMESTAMP], unit="ms")
    return df


def simulate_hedge_trades(df, thresholds=THRESHOLDS, dollar_gamma=DOLLAR_GAMMA):
    thresholds = list(thresholds)
    thresholds.sort()
    hedge_trades = defaultdict(list)
    initial_price = df[CLOSE].iloc[0]
    # last hedged price per threshold
    last_hedge_prices = {t: initial_price for t in thresholds}
    for _, row in df.iterrows():
        current_price = row[CLOSE]
        for threshold in thresholds:
            relative_movement = (
                current_price - last_hedge_prices[threshold]
            ) / last_hedge_prices[threshold]
            if abs(relative_movement) >= threshold:
                delta_exposure = dollar_gamma * relative_movement * 100
                hedge_size = -delta_exposure / current_price
                hedge_trades[threshold].append(
                    {
                        TIMESTAMP: row[TIMESTAMP],
                        PRICE: current_price,
                        QUANTITY: hedge_size,
                    }
                )
                last_hedge_prices[threshold] = current_price
    return {
        t: pd.DataFrame(hedge_trades[t], columns=[TIMESTAMP, PRICE, QUANTITY])
        for t in thresholds
    }


def run():
    spot_data = fetch_binance_data()
    hedge_trades_per_threshold = simulate_hedge_trades(spot_data)
    pnl_per_threshold = compute_all_pnls(
        spot_data,
        hedge_trades_per_threshold,
        transaction_cost=0,
    )
    plot(
        hedge_trades_per_threshold,
        pnl_per_threshold,
        spot_data[TIMESTAMP],
        transaction_cost=0,
    )
    export_table(hedge_trades_per_threshold, pnl_per_threshold, transaction_cost=0)
    pnl_per_threshold = compute_all_pnls(
        spot_data,
        hedge_trades_per_threshold,
    )
    plot(
        hedge_trades_per_threshold,
        pnl_per_threshold,
        spot_data[TIMESTAMP],
    )
    export_table(hedge_trades_per_threshold, pnl_per_threshold)


if __name__ == "__main__":
    run()
