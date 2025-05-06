import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Define the ticker symbol and timeframe
ticker = "BTC-USD"
period = "1mo"
interval = "1h"

# Download the data from yfinance
data = yf.download(ticker, period=period, interval=interval)

# Calculate the short-term (20-hour) and long-term (50-hour) Simple Moving Averages
data['SMA_20'] = data['Close'].rolling(window=20).mean()
data['SMA_50'] = data['Close'].rolling(window=50).mean()

# Generate trading signals
data['Signal'] = 0  # Initialize signal column
data['Signal'][data['SMA_20'] > data['SMA_50']] = 1  # Buy signal
data['Signal'][data['SMA_20'] < data['SMA_50']] = -1 # Sell signal

# Generate trade execution based on the signal
data['Position'] = data['Signal'].shift(1) # Shift signal by one period to avoid lookahead bias
data['Trade'] = data['Position'].diff()

# Calculate a simple return based on the strategy (for demonstration)
data['Price_Change'] = data['Close'].pct_change()
data['Strategy_Return'] = data['Position'] * data['Price_Change']
data['Cumulative_Strategy_Return'] = (1 + data['Strategy_Return']).cumprod()

# Plotting the results
plt.figure(figsize=(15, 8))

# Plot the closing price and moving averages
plt.plot(data['Close'], label='BTC/USD Close Price', alpha=0.5)
plt.plot(data['SMA_20'], label='20-hour SMA', alpha=0.7)
plt.plot(data['SMA_50'], label='50-hour SMA', alpha=0.7)

# Plot buy signals
plt.plot(data[data['Trade'] == 1].index, data['SMA_20'][data['Trade'] == 1], '^', markersize=10, color='g', label='Buy Signal')

# Plot sell signals
plt.plot(data[data['Trade'] == -1].index, data['SMA_50'][data['Trade'] == -1], 'v', markersize=10, color='r', label='Sell Signal')

plt.title('BTC/USD Hourly Price with SMA Crossover Strategy')
plt.xlabel('Date and Time')
plt.ylabel('Price (USD)')
plt.legend(loc='upper left')
plt.grid(True)
plt.show()

# Plot the cumulative strategy return
plt.figure(figsize=(15, 5))
plt.plot(data['Cumulative_Strategy_Return'], label='Cumulative Strategy Return')
plt.title('Cumulative Return of SMA Crossover Strategy')
plt.xlabel('Date and Time')
plt.ylabel('Cumulative Return')
plt.legend(loc='upper left')
plt.grid(True)
plt.show()