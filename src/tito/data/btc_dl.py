#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yfinance as yf

ticker = "BTC-USD"

data = yf.download(
    tickers=ticker,
    period="2y",
    interval="1d"
)

data.to_csv("btc_data/daily_2y.csv")