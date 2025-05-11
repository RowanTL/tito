# An implementation of MACD and Bollinger Bands with polars

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from math import sqrt
from pathlib import Path

# %%

# Load data
timespan: str = "2mo"
df_path: Path = Path(f"src/tito/data/btc_data/hourly_6_{timespan}.csv")
#df_path: Path = Path(f"../../data/btc_data/daily_{timespan}.csv")
data = pl.read_csv(df_path, try_parse_dates=True).with_row_index()
col_name: str = "Close"
short_span = 6
long_span = 41
signal_span = 19
transaction_cost = 0.0005
risk_free_rate = 0.0421
#trading_days = 365 # 365 days for daily strategies
trading_days = 1461 # 1461 for 6 hour increments
#trading_days = 730.5 # 730.5 for 12 hour increments
window_size=10

# best sharpe so far for hourly:
# short_span = 15, long_span = 40, signal_span = 9, file is hourly_6_6mo

# %%

# Calculate MACD components
data = data.with_columns((pl.col(col_name).ewm_mean(span=short_span)).alias(f"{col_name}_ewm_{short_span}"))
data = data.with_columns((pl.col(col_name).ewm_mean(span=long_span)).alias(f"{col_name}_ewm_{long_span}"))
data = data.with_columns((pl.col(f"{col_name}_ewm_{short_span}") - pl.col(f"{col_name}_ewm_{long_span}")).alias("MACD_line"))
data = data.with_columns(pl.col("MACD_line").ewm_mean(span=signal_span).alias("signal_line"))

# Calculate Bollinger Bands
sma = data.select(pl.col(col_name).rolling_mean(window_size)).to_series()
smstd = data.select(pl.col(col_name).rolling_std(window_size)).to_series()
upper_band = sma + (2 * smstd)  # Upper band = SMA + 2*standard deviation
lower_band = sma - (2 * smstd)  # Lower band = SMA - 2*standard deviation

# Add Bollinger Bands to the dataframe
data = data.with_columns([
    sma.alias("SMA"),
    upper_band.alias("Upper_Band"),
    lower_band.alias("Lower_Band")
])

# Calculate histogram values (MACD line - signal line)
data = data.with_columns((pl.col("MACD_line") - pl.col("signal_line")).alias("histogram"))

# Time to introduce signals
# Buy when MACD_line > signal_line AND standard deviation < closing price
positions = data.select(pl.when((pl.col("MACD_line") > pl.col("signal_line")) & (lower_band <= pl.col(col_name)))
                            .then(1)
                            .otherwise(0)
                            .alias("positions")).to_series()

# Add positions to the dataframe
data = data.with_columns(positions.alias("positions"))

# Calculate position changes to identify buy/sell signals
data = data.with_columns(
    (pl.col("positions") - pl.col("positions").shift(1).fill_null(0)).alias("position_change")
)

dailyret = data.select((pl.col(col_name).pct_change()).alias("dailyret")).to_series()
excessret = dailyret - risk_free_rate / trading_days
# profit and loss
pnl_per = positions.shift() * excessret
all_transaction_costs = abs(pnl_per) * transaction_cost
# profit and loss with transaction costs
pnl_t = (pnl_per - all_transaction_costs)
total_pnl = pnl_t.sum()
sharpe_set = sqrt(trading_days) * pnl_t[1:].mean() / pnl_t[1:].std()

print(f"Total pnl: {total_pnl}")
print(f"Sharpe ratio: {sharpe_set}")

# %%

fig, ax = plt.subplots()
ax.plot(pnl_t.cum_sum())
ax.set_title("MACD and BB profit and loss cummulative sum")
ax.set_ylabel("cumulative profit")
ax.set_xlabel("Hour (Increments of 6)")
plt.show()

# %%

fig, ax = plt.subplots()
ax.plot(data["MACD_line"], color="blue")
ax.plot(data["signal_line"], color="red")
ax.set_title("MACD_line and signal_line comparision")
ax.legend(["MACD_line", "signal_line"])
plt.show()

# %%

# Sort data by index to ensure proper line connection
sorted_data = data.sort("index")

fig, ax = plt.subplots(figsize=(12, 6))

# Plot all data as a single connected line
ax.plot(sorted_data["index"], sorted_data[col_name], color="gray", linewidth=1.5, alpha=0.5)

# Plot buy points (positions == 1) in green
buy_data = data.filter(positions == 1)
ax.scatter(buy_data["index"], buy_data[col_name], color="green", s=30, label="Buy Signal")

# Plot sell points (positions == 0) in red
sell_data = data.filter(positions == 0)
ax.scatter(sell_data["index"], sell_data[col_name], color="red", s=30, label="Sell Signal")

ax.set_title(f"BTC closing price for the last {timespan}")
ax.set_ylabel("Price in USD")
ax.set_xlabel("Hour (Increments of 6)")
ax.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()