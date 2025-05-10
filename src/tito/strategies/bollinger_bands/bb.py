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

# %%

# Create a new figure with a specified size
plt.figure(figsize=(12, 8))

# Plot the actual price
plt.plot(data[col_name], label='BTC Price', color='blue', alpha=0.6)

# Plot the SMA
plt.plot(sma, label=f'SMA-{window_size}', color='red', linewidth=2)

# Plot the bands (SMA ± SMSTD)
upper_band = sma + 2 * smstd
lower_band = sma - 2 * smstd
plt.plot(upper_band, label=f'SMA+STD ({window_size})', color='green', linestyle='--')
plt.plot(lower_band, label=f'SMA-STD ({window_size})', color='green', linestyle='--')

# Fill the area between the bands
plt.fill_between(range(len(data)), upper_band, lower_band, color='green', alpha=0.1)

# Add title and labels
plt.title(f'BTC Price with Simple Moving Average and Standard Deviation ({timespan})')
plt.xlabel('Hours')
plt.ylabel('Price (USD)')
plt.legend()
plt.grid(True, alpha=0.3)

# Show the plot
plt.tight_layout()
plt.show()

# %%

# Alternative visualization with two subplots
fig = plt.figure(figsize=(14, 10))
gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])

# Top subplot for price and SMA
ax1 = plt.subplot(gs[0])
ax1.plot(data[col_name], label='BTC Price', color='blue', alpha=0.6)
ax1.plot(sma, label=f'SMA-{window_size}', color='red', linewidth=2)
ax1.plot(upper_band, label=f'SMA+STD ({window_size})', color='green', linestyle='--')
ax1.plot(lower_band, label=f'SMA-STD ({window_size})', color='green', linestyle='--')
ax1.fill_between(range(len(data)), upper_band, lower_band, color='green', alpha=0.1)
ax1.set_title(f'BTC Price with Simple Moving Average and Standard Deviation ({timespan})')
ax1.set_ylabel('Price (USD)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Bottom subplot for standard deviation
ax2 = plt.subplot(gs[1], sharex=ax1)
ax2.plot(smstd, label=f'Standard Deviation ({window_size})', color='purple')
ax2.set_xlabel('Hours')
ax2.set_ylabel('Standard Deviation')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()