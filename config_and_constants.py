from datetime import UTC, datetime
from pathlib import Path

# Coupled Configuration Parameters
DATA_INTERVAL = "1m"  # Don't change without adjusting `INTERVALS_PER_DAY`.
INTERVALS_PER_DAY = 60 * 24  # Don't change without adjusting `DATA_INTERVAL`.

# Configuration Parameters
TRADING_PAIR = "SOL/USDT"
START = datetime(year=2025, month=1, day=17, hour=8, tzinfo=UTC)
END = datetime(year=2025, month=1, day=21, hour=8, tzinfo=UTC)
DOLLAR_GAMMA = -100_000
DAILY_THETA_DECAY = 20_000
TRANSACTION_COST = 0.0005
THETA_DECAY_PER_INTERVAL = DAILY_THETA_DECAY / INTERVALS_PER_DAY
LOG_SCALE = True
PLOT_BASE_FOLDER = Path("plots")
HEDGE_FOLDER = Path("hedge_quantity_and_position_over_time")
PNL_FOLDER = Path("total_and_delta_pnl_over_time")
# These thresholds grow by a roughly constant factor, which therefore scales hedge frequency also by a roughly constant factor.
THRESHOLDS = (
    0.001,
    0.0015,
    0.0022,
    0.0033,
    0.005,
    0.007,
    0.01,
    0.015,
    0.022,
    0.033,
    0.05,
    0.07,
    0.1,
    0.15,
    0.22,
    0.33,
    0.50,
)

# Reused String Literals
TIMESTAMP = "timestamp"
CLOSE = "close"
PRICE = "price"
QUANTITY = "quantity"
DELTA_PNL = "delta_pnl"
GAMMA_PNL = "gamma_pnl"
THETA_PNL = "theta_pnl"
TOTAL_PNL = "total_pnl"
