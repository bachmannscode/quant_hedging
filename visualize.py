from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import table

from config_and_constants import (
    DELTA_PNL,
    GAMMA_PNL,
    HEDGE_FOLDER,
    LOG_SCALE,
    PLOT_BASE_FOLDER,
    PNL_FOLDER,
    PRICE,
    QUANTITY,
    THETA_PNL,
    THRESHOLDS,
    TIMESTAMP,
    TOTAL_PNL,
    TRANSACTION_COST,
)
from util import compute_max_drawdown


def plot_total_pnl_over_threshold(pnl_per_threshold, save_path):
    # `/` operator on pathlib.Path
    save_path /= "pnl_vs_threshold"
    total_pnls = {
        threshold: df[TOTAL_PNL].iloc[-1] for threshold, df in pnl_per_threshold.items()
    }
    plt.figure()
    ax = (
        pd.Series(total_pnls)
        .sort_index()
        .plot(
            kind="line",
            marker="o",
            title="Total PnL vs Rehedge Threshold",
            xlabel="Rehedge Threshold (Relative Move)",
            ylabel="Total PnL ($)",
            grid=True,
        )
    )
    if LOG_SCALE:
        ax.set_xscale("log")
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_max_drawdown_over_threshold(pnl_per_threshold, save_path):
    # `/` operator on pathlib.Path
    save_path /= "drawdown_vs_threshold"
    max_drawdowns = {
        threshold: compute_max_drawdown(df[TOTAL_PNL])
        for threshold, df in pnl_per_threshold.items()
    }
    plt.figure()
    ax = (
        pd.Series(max_drawdowns)
        .sort_index()
        .plot(
            kind="line",
            marker="o",
            title="Max Drawdown vs Rehedge Threshold",
            xlabel="Rehedge Threshold (Relative Move)",
            ylabel="Max Drawdown ($)",
            grid=True,
        )
    )
    if LOG_SCALE:
        ax.set_xscale("log")
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_trade_count_over_threshold(hedge_trades_per_threshold, save_path):
    # `/` operator on pathlib.Path
    save_path /= "trade_count_vs_threshold"
    trade_counts = {
        threshold: len(df) for threshold, df in hedge_trades_per_threshold.items()
    }
    plt.figure()
    ax = (
        pd.Series(trade_counts)
        .sort_index()
        .plot(
            kind="line",
            marker="o",
            title="Trade Count vs Rehedge Threshold",
            xlabel="Rehedge Threshold (Relative Move)",
            ylabel="Number of Hedge Trades",
            grid=True,
        )
    )
    if LOG_SCALE:
        ax.set_xscale("log")
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_tx_cost_over_threshold(
    hedge_trades_per_threshold, save_path, transaction_cost
):
    # `/` operator on pathlib.Path
    save_path /= "tx_cost_vs_threshold"
    tx_costs = {
        threshold: (df[QUANTITY].abs() * df[PRICE] * transaction_cost).sum()
        for threshold, df in hedge_trades_per_threshold.items()
    }
    plt.figure()
    ax = (
        pd.Series(tx_costs)
        .sort_index()
        .plot(
            kind="line",
            marker="o",
            title="Total Transaction Cost vs Rehedge Threshold",
            xlabel="Rehedge Threshold (Relative Move)",
            ylabel="Total Transaction Cost ($)",
            grid=True,
        )
    )
    if LOG_SCALE:
        ax.set_xscale("log")
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_theta_and_gamma_pnl_over_time(
    pnl_per_threshold,
    save_path,
):
    save_path /= "theta_and_gamma_pnl_over_time"
    df = next(iter(pnl_per_threshold.values()))

    plt.figure()
    # aggregate to less samples for better plot UX
    df[THETA_PNL].resample("1h").last().plot(label="Theta PnL", marker=".")
    # aggregate to less samples for better plot UX
    df[GAMMA_PNL].resample("1h").last().plot(label="Gamma PnL", marker=".")

    plt.title(f"PnL Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("PnL ($)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_tot_and_delta_pnl_over_time(
    pnl_per_threshold,
    threshold,
    threshold_idx,
    save_path,
):
    # `/` operator on pathlib.Path
    save_path /= f"{threshold_idx}_th_{str(threshold).split('.')[-1]}"
    df = pnl_per_threshold[threshold]

    plt.figure()
    # aggregate to less samples for better plot UX
    df[TOTAL_PNL].resample("1h").last().plot(label="Total PnL", marker=".")
    # aggregate to less samples for better plot UX
    df[DELTA_PNL].resample("1h").last().plot(label="Delta PnL", marker=".")

    plt.title(f"PnL Over Time (Threshold {threshold})")
    plt.xlabel("Timestamp")
    plt.ylabel("PnL ($)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_hedge_quantity_and_position_over_time(
    hedge_trades_per_threshold,
    spot_timestamps,
    threshold,
    threshold_idx,
    save_path,
):
    # `/` operator on pathlib.Path
    save_path /= f"{threshold_idx}_th_{str(threshold).split('.')[-1]}"
    hedge_trades = hedge_trades_per_threshold[threshold]

    # Align trades to full spot timeline
    quantities = pd.Series(0.0, index=spot_timestamps)
    if not hedge_trades.empty:
        quantities.loc[hedge_trades[TIMESTAMP]] = hedge_trades[QUANTITY].values
    # aggregate to less samples for better plot UX
    quantities = quantities.resample("1h").sum()
    # aggregate to less samples for better plot UX
    cumulative = quantities.cumsum().resample("1h").sum()

    plt.figure()
    quantities.plot(label="Hedge Trade Quantity", marker=".")
    cumulative.plot(label="Cumulative Hedge Position", marker=".")

    plt.title(f"Hedge Quantity and Position Over Time (Threshold {threshold})")
    plt.xlabel("Timestamp")
    plt.ylabel("Quantity")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def export_table(
    hedge_trades_per_threshold, pnl_per_threshold, transaction_cost=TRANSACTION_COST
):
    table_base_path = Path("summary_table")
    table_path = (
        f"{table_base_path}_tx_cost_zero"
        if transaction_cost == 0
        else f"{table_base_path}_tx_cost_{str(transaction_cost).split('.')[-1]}"
    )
    summary_data = []
    for threshold in THRESHOLDS:
        pnl_df = pnl_per_threshold[threshold]
        trades_df = hedge_trades_per_threshold[threshold]

        total_pnl = pnl_df[TOTAL_PNL].iloc[-1]
        max_dd = compute_max_drawdown(pnl_df[TOTAL_PNL])
        trade_count = len(trades_df)

        summary_data.append((threshold, total_pnl, max_dd, trade_count))
    summary_df = pd.DataFrame(
        summary_data, columns=["Threshold", "Total PnL", "Max Drawdown", "Trade Count"]
    )
    summary_df.set_index("Threshold", inplace=True)

    _, ax = plt.subplots(figsize=(10, len(summary_df) * 0.4 + 1))
    ax.axis("off")
    tbl = table(ax, summary_df.round(2), loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.2, 1.2)

    title = "Hedging Performance Summary"
    if transaction_cost == 0:
        plt.title(title + " with no Transaction Cost", fontsize=14, pad=20)
    else:
        plt.title(
            title + f" with {transaction_cost} Transaction Cost", fontsize=14, pad=20
        )
    plt.tight_layout()
    plt.savefig(table_path)
    plt.close()


def plot(
    hedge_trades_per_threshold,
    pnl_per_threshold,
    timestamps,
    transaction_cost=TRANSACTION_COST,
):
    plot_folder = Path(
        f"{PLOT_BASE_FOLDER}_tx_cost_zero"
        if transaction_cost == 0
        else f"{PLOT_BASE_FOLDER}_tx_cost_{str(transaction_cost).split('.')[-1]}"
    )
    plot_folder.mkdir(exist_ok=True)
    plot_total_pnl_over_threshold(pnl_per_threshold, plot_folder)
    plot_max_drawdown_over_threshold(pnl_per_threshold, plot_folder)
    plot_trade_count_over_threshold(hedge_trades_per_threshold, plot_folder)
    plot_tx_cost_over_threshold(
        hedge_trades_per_threshold, plot_folder, transaction_cost
    )
    plot_theta_and_gamma_pnl_over_time(pnl_per_threshold, plot_folder)
    hedge_folder = Path(plot_folder / HEDGE_FOLDER)
    hedge_folder.mkdir(exist_ok=True)
    for th_idx, threshold in enumerate(THRESHOLDS, start=1):
        plot_hedge_quantity_and_position_over_time(
            hedge_trades_per_threshold, timestamps, threshold, th_idx, hedge_folder
        )
    pnl_folder = Path(plot_folder / PNL_FOLDER)
    pnl_folder.mkdir(exist_ok=True)
    for th_idx, threshold in enumerate(THRESHOLDS, start=1):
        plot_tot_and_delta_pnl_over_time(
            pnl_per_threshold, threshold, th_idx, pnl_folder
        )
