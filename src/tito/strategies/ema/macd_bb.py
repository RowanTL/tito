# An implementation of MACD and Bollinger Bands with polars

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from math import sqrt
from pathlib import Path

# %%

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

# Convert to pandas for plotting
plot_df = data.to_pandas()

# %%

# Create plot with 3 subplots - price with Bollinger Bands on top, 
# positions in middle, MACD with histogram at bottom
plt.figure(figsize=(14, 14))
gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 2])

# Price chart with Bollinger Bands
ax1 = plt.subplot(gs[0])
ax1.plot(plot_df["Datetime"], plot_df[col_name], label="Bitcoin Price", color="black")
ax1.plot(plot_df["Datetime"], plot_df["SMA"], label=f"SMA ({window_size})", color="blue")
ax1.plot(plot_df["Datetime"], plot_df["Upper_Band"], label="Upper Band (2σ)", color="green", linestyle="--")
ax1.plot(plot_df["Datetime"], plot_df["Lower_Band"], label="Lower Band (2σ)", color="green", linestyle="--")

# Fill the area between the bands
ax1.fill_between(plot_df["Datetime"], plot_df["Upper_Band"], plot_df["Lower_Band"], color="green", alpha=0.1)

# Add buy and sell signals
buy_signals = plot_df[plot_df["position_change"] == 1]
sell_signals = plot_df[plot_df["position_change"] == -1]

ax1.scatter(buy_signals["Datetime"], buy_signals[col_name], marker="^", color="green", s=100, label="Buy Signal")
ax1.scatter(sell_signals["Datetime"], sell_signals[col_name], marker="v", color="red", s=100, label="Sell Signal")

ax1.set_title(f"Bitcoin Price with Bollinger Bands ({timespan})")
ax1.set_ylabel("Price (USD)")
ax1.grid(True)
ax1.legend(loc="upper left")

# Position chart
ax2 = plt.subplot(gs[1], sharex=ax1)
ax2.plot(plot_df["Datetime"], plot_df["positions"], label="Position (1=Long, 0=Flat)", color="purple", drawstyle="steps-post")
ax2.set_ylabel("Position")
ax2.set_ylim(-0.1, 1.1)
ax2.grid(True)
ax2.legend()

# MACD with histogram
ax3 = plt.subplot(gs[2], sharex=ax1)
ax3.plot(plot_df["Datetime"], plot_df["MACD_line"], label="MACD Line", color="blue")
ax3.plot(plot_df["Datetime"], plot_df["signal_line"], label="Signal Line", color="red")

# Add histogram bars
histogram = plot_df["histogram"]
pos_hist = histogram.copy()
neg_hist = histogram.copy()
pos_hist[pos_hist <= 0] = 0
neg_hist[neg_hist > 0] = 0

# Plot positive and negative histogram values with different colors
ax3.bar(plot_df["Datetime"], pos_hist, color="green", alpha=0.5, width=1)
ax3.bar(plot_df["Datetime"], neg_hist, color="red", alpha=0.5, width=1)

# Add horizontal line at y=0
ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)

ax3.set_title("MACD with Histogram")
ax3.set_xlabel("Date")
ax3.set_ylabel("MACD")
ax3.grid(True)
ax3.legend()

plt.tight_layout()
plt.show()

# %%

# Create a combined plot with just price and MACD
plt.figure(figsize=(14, 10))
gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])

# Price chart with Bollinger Bands
ax1 = plt.subplot(gs[0])
ax1.plot(plot_df["Datetime"], plot_df[col_name], label="Bitcoin Price", color="black")
ax1.plot(plot_df["Datetime"], plot_df["SMA"], label=f"SMA ({window_size})", color="blue")
ax1.plot(plot_df["Datetime"], plot_df["Upper_Band"], label="Upper Band (2σ)", color="green", linestyle="--")
ax1.plot(plot_df["Datetime"], plot_df["Lower_Band"], label="Lower Band (2σ)", color="green", linestyle="--")

# Fill the area between the bands
ax1.fill_between(plot_df["Datetime"], plot_df["Upper_Band"], plot_df["Lower_Band"], color="green", alpha=0.1)

# Add buy and sell signals
buy_signals = plot_df[plot_df["position_change"] == 1]
sell_signals = plot_df[plot_df["position_change"] == -1]

ax1.scatter(buy_signals["Datetime"], buy_signals[col_name], marker="^", color="green", s=100, label="Buy Signal")
ax1.scatter(sell_signals["Datetime"], sell_signals[col_name], marker="v", color="red", s=100, label="Sell Signal")

ax1.set_title(f"Bitcoin Price with Bollinger Bands and Trading Signals ({timespan})")
ax1.set_ylabel("Price (USD)")
ax1.grid(True)
ax1.legend(loc="upper left")

# MACD with histogram
ax2 = plt.subplot(gs[1], sharex=ax1)
ax2.plot(plot_df["Datetime"], plot_df["MACD_line"], label="MACD Line", color="blue")
ax2.plot(plot_df["Datetime"], plot_df["signal_line"], label="Signal Line", color="red")

# Add histogram bars
ax2.bar(plot_df["Datetime"], pos_hist, color="green", alpha=0.5, width=1, label="Positive Histogram")
ax2.bar(plot_df["Datetime"], neg_hist, color="red", alpha=0.5, width=1, label="Negative Histogram")

# Add horizontal line at y=0
ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)

ax2.set_title("MACD with Histogram")
ax2.set_xlabel("Date")
ax2.set_ylabel("MACD")
ax2.grid(True)
ax2.legend()

plt.tight_layout()
plt.show()

# %%

# Strategy performance visualization - just the price chart with signals
plt.figure(figsize=(14, 8))

# Price chart with buy/sell signals and Bollinger Bands
plt.plot(plot_df["Datetime"], plot_df[col_name], label="Bitcoin Price", color="black")
plt.plot(plot_df["Datetime"], plot_df["SMA"], label=f"SMA ({window_size})", color="blue")
plt.plot(plot_df["Datetime"], plot_df["Upper_Band"], label="Upper Band (2σ)", color="green", linestyle="--")
plt.plot(plot_df["Datetime"], plot_df["Lower_Band"], label="Lower Band (2σ)", color="green", linestyle="--")

# Fill the area between the bands
plt.fill_between(plot_df["Datetime"], plot_df["Upper_Band"], plot_df["Lower_Band"], color="green", alpha=0.1)

# Add buy and sell signals
plt.scatter(buy_signals["Datetime"], buy_signals[col_name], marker="^", color="green", s=100, label="Buy Signal")
plt.scatter(sell_signals["Datetime"], sell_signals[col_name], marker="v", color="red", s=100, label="Sell Signal")

# Add strategy performance metrics as text
performance_text = (
    f"Total PnL: {total_pnl:.4f}\n"
    f"Sharpe Ratio: {sharpe_set:.4f}\n"
    f"Risk-Free Rate: {risk_free_rate:.4f}\n"
    f"Transaction Cost: {transaction_cost:.4f}"
)
plt.text(0.02, 0.02, performance_text, transform=plt.gca().transAxes,
        bbox=dict(facecolor='white', alpha=0.8), fontsize=10)

plt.title(f"Bitcoin Price with Bollinger Bands and Trading Signals ({timespan})")
plt.ylabel("Price (USD)")
plt.xlabel("Date")
plt.grid(True)
plt.legend(loc="upper left")

plt.tight_layout()
plt.show()