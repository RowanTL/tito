# The efficiency ratio (ER) is a means of measuring random noise in the market.
# Noise is classified as erratic movement that makes up the pattern of any
# price series. High noise very random, low noise straight line.
# Do non confuse noise with volatility.

import polars as pl
from pathlib import Path

# %%

# Load data
timespan: str = "2mo"
df_path: Path = Path(f"src/tito/data/btc_data/hourly_6_{timespan}.csv")
#df_path: Path = Path(f"../../data/btc_data/daily_{timespan}.csv")
data = pl.read_csv(df_path)
col_name: str = "Close"

# %%

# Efficiency ratio = ( abs(net change in price) ) / ( sum of individual price changes as positive numbers )
# This definition is kinda ambiguous :/ Just used the math equation instead :shrug:

# Old definition that's wrong, do not use
"""
price_change = data.select(pl.col(col_name).pct_change()).to_series().fill_null(0)
net_price_change = abs(price_change.first() - price_change.last())
abs_price_change = abs(price_change)
sum_ind_abs_price_change = abs_price_change.sum()
efficiency_ratio = net_price_change / sum_ind_abs_price_change
"""

abs_net_price_change = abs(data[col_name].first() - data[col_name].last())
ind_change_positive = data.select(pl.col(col_name) - pl.col(col_name).shift(1)).to_series().abs()
sum_ind_abs_price_change = ind_change_positive.sum()
efficiency_ratio = abs_net_price_change / sum_ind_abs_price_change

print(efficiency_ratio)