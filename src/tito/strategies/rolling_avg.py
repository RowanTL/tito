#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yfinance as yf
import polars as pl
import pandas as pd
import numpy as np

data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
df = pd.DataFrame(data, columns=['A', 'B', 'C'])
print(df)