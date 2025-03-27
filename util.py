import pandas as pd

from config_and_constants import (
    CLOSE,
    DELTA_PNL,
    DOLLAR_GAMMA,
    GAMMA_PNL,
    PRICE,
    QUANTITY,
    THETA_DECAY_PER_INTERVAL,
    THETA_PNL,
    TIMESTAMP,
    TOTAL_PNL,
    TRANSACTION_COST,
)


def cumulative_theta_pnl(spot_timestamps, decay_per_interval=THETA_DECAY_PER_INTERVAL):
    df = pd.DataFrame({TIMESTAMP: spot_timestamps})
    df[THETA_PNL] = pd.RangeIndex(len(df)) * decay_per_interval
    return df


def cumulative_delta_pnl(spot_timestamps, hedge_trades, final_price, transaction_cost):
    total_pnl = 0
    long_position = 0
    long_avg_price = 0  # Weighted average buy price
    short_position = 0
    short_avg_price = 0  # Weighted average sell price

    df = pd.DataFrame({TIMESTAMP: spot_timestamps, DELTA_PNL: None})
    hedge_idx = 0  # Index to track hedge trades

    for i, timestamp in enumerate(spot_timestamps):

        # Process hedge trade if the timestamp matches
        if (
            hedge_idx < len(hedge_trades)
            and hedge_trades[TIMESTAMP].iloc[hedge_idx] == timestamp
        ):
            price = hedge_trades[PRICE].iloc[hedge_idx]
            quantity = hedge_trades[QUANTITY].iloc[hedge_idx]
            trade_pnl = 0
            trade_cost = abs(quantity) * price * transaction_cost

            if quantity > 0:  # Buying (increasing long position or closing a short)
                if short_position > 0:  # Closing short position first
                    if quantity >= short_position:  # Fully close short
                        trade_pnl += short_position * (short_avg_price - price)
                        quantity -= short_position
                        short_position = 0
                    else:  # Partially close short
                        trade_pnl += quantity * (short_avg_price - price)
                        short_position -= quantity
                        quantity = 0

                if quantity > 0:  # Remaining quantity increases long position
                    new_long_position = long_position + quantity
                    long_avg_price = (
                        long_avg_price * long_position + price * quantity
                    ) / new_long_position
                    long_position = new_long_position

            elif quantity < 0:  # Selling (increasing short position or closing a long)
                quantity = -quantity  # Work with absolute values

                if long_position > 0:  # Closing long position first
                    if quantity >= long_position:  # Fully close long
                        trade_pnl += long_position * (price - long_avg_price)
                        quantity -= long_position
                        long_position = 0
                    else:  # Partially close long
                        trade_pnl += quantity * (price - long_avg_price)
                        long_position -= quantity
                        quantity = 0

                if quantity > 0:  # Remaining quantity increases short position
                    new_short_position = short_position + quantity
                    short_avg_price = (
                        short_avg_price * short_position + price * quantity
                    ) / new_short_position
                    short_position = new_short_position

            total_pnl += trade_pnl - trade_cost
            hedge_idx += 1  # Move to the next hedge trade

        df.loc[i, DELTA_PNL] = total_pnl

    # Add unrealized PnL at final price
    if long_position > 0:
        total_pnl += long_position * (final_price - long_avg_price)
    if short_position > 0:
        total_pnl += short_position * (short_avg_price - final_price)

    df.loc[df.index[-1], DELTA_PNL] = total_pnl  # Ensure final timestamp has final PnL

    return df


def cumulative_gamma_pnl(spot_data, dollar_gamma=DOLLAR_GAMMA):
    df = pd.DataFrame({TIMESTAMP: spot_data[TIMESTAMP]})
    df[GAMMA_PNL] = [
        dollar_gamma * (spot_price / spot_data[CLOSE].iloc[0] - 1) ** 2 * 100 / 2
        for spot_price in spot_data[CLOSE]
    ]
    return df


def compute_all_pnls(
    spot_data, hedge_trades_per_threshold, transaction_cost=TRANSACTION_COST
):
    # Compute once, same for all thresholds
    gamma_pnl = cumulative_gamma_pnl(spot_data)
    theta_pnl = cumulative_theta_pnl(spot_data[TIMESTAMP])

    result = {}
    for threshold, hedge_trades in hedge_trades_per_threshold.items():
        delta_pnl = cumulative_delta_pnl(
            spot_data[TIMESTAMP],
            hedge_trades,
            spot_data[CLOSE].iloc[-1],
            transaction_cost,
        )

        # Have gamma & theta pnl duplicated for easier plotting
        df = pd.DataFrame(
            {
                TIMESTAMP: spot_data[TIMESTAMP],
                DELTA_PNL: delta_pnl[DELTA_PNL],
                GAMMA_PNL: gamma_pnl[GAMMA_PNL],
                THETA_PNL: theta_pnl[THETA_PNL],
            }
        )
        df.set_index(TIMESTAMP, inplace=True)
        df[TOTAL_PNL] = df[[THETA_PNL, DELTA_PNL, GAMMA_PNL]].sum(axis=1)
        result[threshold] = df

    return result


def compute_max_drawdown(pnl_series):
    cumulative_max = pnl_series.cummax()
    drawdown = cumulative_max - pnl_series
    return drawdown.max()
