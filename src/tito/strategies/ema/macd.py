#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Am implementation of MACD with polars

# %%

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from math import sqrt
from pathlib import Path

# %%

# Load data
timespan: str = "6mo"
df_path: Path = Path(f"../../data/btc_data/hourly_6_{timespan}.csv")
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

# best sharpe so far for hourly: 
# short_span = 15, long_span = 40, signal_span = 9, file is hourly_6_6mo

# %%

# Calculate MACD components
data = data.with_columns((pl.col(col_name).ewm_mean(span=short_span)).alias(f"{col_name}_ewm_{short_span}"))
data = data.with_columns((pl.col(col_name).ewm_mean(span=long_span)).alias(f"{col_name}_ewm_{long_span}"))
data = data.with_columns((pl.col(f"{col_name}_ewm_{short_span}") - pl.col(f"{col_name}_ewm_{long_span}")).alias("MACD_line"))
data = data.with_columns(pl.col("MACD_line").ewm_mean(span=signal_span).alias("signal_line"))

# Calculate histogram values (MACD line - signal line)
data = data.with_columns((pl.col("MACD_line") - pl.col("signal_line")).alias("histogram"))

# Time to introduce signals
positions = data.select(pl.when(pl.col("MACD_line") > pl.col("signal_line"))
                            .then(1)
                            .otherwise(0)
                            .alias("positions")).to_series()

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

# Create plot with 2 subplots - price on top, MACD with histogram below
plt.figure(figsize=(14, 10))
gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])

# Price chart
ax1 = plt.subplot(gs[0])
ax1.plot(plot_df["Datetime"], plot_df[col_name], label="Bitcoin Price", color="black")
ax1.set_title(f"Bitcoin Price ({timespan})")
ax1.set_ylabel("Price")
ax1.grid(True)
ax1.legend()

# MACD with histogram
ax2 = plt.subplot(gs[1], sharex=ax1)
ax2.plot(plot_df["Datetime"], plot_df["MACD_line"], label="MACD Line", color="blue")
ax2.plot(plot_df["Datetime"], plot_df["signal_line"], label="Signal Line", color="red")

# Add histogram bars
histogram = plot_df["histogram"]
pos_hist = histogram.copy()
neg_hist = histogram.copy()
pos_hist[pos_hist <= 0] = 0
neg_hist[neg_hist > 0] = 0

# Plot positive and negative histogram values with different colors
ax2.bar(plot_df["Datetime"], pos_hist, color="green", alpha=0.5, width=1)
ax2.bar(plot_df["Datetime"], neg_hist, color="red", alpha=0.5, width=1)

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

# If you prefer to see just the MACD components without the price chart:
plt.figure(figsize=(14, 6))

# MACD and signal lines
plt.plot(plot_df["Datetime"], plot_df["MACD_line"], label="MACD Line", color="blue")
plt.plot(plot_df["Datetime"], plot_df["signal_line"], label="Signal Line", color="red")

# Add histogram bars
pos_hist = histogram.copy()
neg_hist = histogram.copy()
pos_hist[pos_hist <= 0] = 0
neg_hist[neg_hist > 0] = 0

plt.bar(plot_df["Datetime"], pos_hist, color="green", alpha=0.5, width=1, label="Positive Histogram")
plt.bar(plot_df["Datetime"], neg_hist, color="red", alpha=0.5, width=1, label="Negative Histogram")

# Add horizontal line at y=0
plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)

plt.title(f"MACD with Histogram - Bitcoin ({timespan})")
plt.xlabel("Date")
plt.ylabel("MACD")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
