import polars as pl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from math import sqrt
from pathlib import Path

# %%

# Type %reset into ipython to delete all variables

# Load data
timespan: str = "6mo"
df_path: Path = Path(f"src/tito/data/btc_data/hourly_6_{timespan}.csv")
#df_path: Path = Path(f"../../data/btc_data/daily_{timespan}.csv")
data = pl.read_csv(df_path)
col_name: str = "Close"
short_span = 6
long_span = 41
signal_span = 19
transaction_cost = 0.0005
risk_free_rate = 0.0421
#trading_days = 365 # 365 days for daily strategies
trading_days = 1461 # 1461 for 6 hour increments
#trading_days = 730.5 # 730.5 for 12 hour increments
window_size = 20

# %%

sma = data.select(pl.col(col_name).rolling_mean(window_size)).to_series()
smstd = data.select(pl.col(col_name).rolling_std(window_size)).to_series()
