#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yfinance as yf
import polars as pl
from datetime import datetime, timedelta

# Define the ticker
ticker = 'BTC-USD'

# Define the date range: last 30 days up to now
end = datetime.utcnow()
start = end - timedelta(days=30)

# Download 6-hour interval data
data = yf.download(
    ticker,
    start=start.strftime('%Y-%m-%d'),
    end=end.strftime('%Y-%m-%d'),
    interval='6h',
    progress=True
)

# Ensure datetime is in UTC
data.index = data.index.tz_localize('UTC') if data.index.tz is None else data.index.tz_convert('UTC')

# Optional: Filter to only rows centered around midnight UTC (e.g. 00:00, 06:00, 12:00, 18:00 UTC)
# Since 6h intervals are already aligned to those, we can just inspect:
print(data.head(10))
