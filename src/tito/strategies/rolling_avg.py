import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- Configuration ---
ticker = 'BTC-USD'
# Calculate date range for the last 2 years
end_date = datetime.now()
#start_date = end_date - timedelta(days=2*365)

# going for hour data here
start_date = end_date - timedelta(days=60)

# SMA periods
short_window = 10  # Short-term SMA (e.g., 20 days)
long_window = 40   # Long-term SMA (e.g., 50 days)

# --- Risk and Cost Parameters ---
annual_risk_free_rate = 0.0421 # 4.21% expressed as a decimal
transaction_cost_bps = 0.005   # 0.005 basis points per transaction
# Convert basis points to decimal: bps / 10000
transaction_cost_rate = transaction_cost_bps / 10000.0
annualization_factor = 365 # Trading days in a year (use 252 or 365)

# Calculate daily risk-free rate
# Daily Rate = (1 + Annual Rate)^(1 / N) - 1
daily_rf_rate = (1 + annual_risk_free_rate)**(1/annualization_factor) - 1

print(f"--- Parameters ---")
print(f"Ticker: {ticker}")
print(f"Analysis Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print(f"SMA Windows: {short_window} / {long_window}")
print(f"Annual Risk-Free Rate: {annual_risk_free_rate:.4%}")
print(f"Daily Risk-Free Rate: {daily_rf_rate:.8f}")
print(f"Transaction Cost: {transaction_cost_bps} bps per trade ({transaction_cost_rate:.8f})")
print(f"Annualization Factor: {annualization_factor}")
print(f"------------------")

# --- Step 1: Fetch Data ---
print(f"\nFetching {ticker} data...")
try:
    #data = yf.download(ticker, start=start_date, end=end_date, interval='1d')
    data = yf.download(ticker, period="6mo", interval='1h')
    if data.empty:
        print(f"No data downloaded for {ticker}. Check the ticker symbol or date range.")
        exit()
    print("Data downloaded successfully.")
except Exception as e:
    print(f"Error downloading data: {e}")
    exit()

# --- Step 2: Calculate SMAs ---
print(f"Calculating {short_window}-day and {long_window}-day SMAs...")
price_col = 'Close' # Use 'Close' price
data[f'SMA_{short_window}'] = data[price_col].rolling(window=short_window, min_periods=1).mean()
data[f'SMA_{long_window}'] = data[price_col].rolling(window=long_window, min_periods=1).mean()
print("SMAs calculated.")

# --- Step 3: Generate Trading Signals ---
print("Generating trading signals based on SMA crossover...")
data['Signal'] = 0.0
data.loc[data.index[long_window:], 'Signal'] = np.where(
    data[f'SMA_{short_window}'][long_window:] > data[f'SMA_{long_window}'][long_window:], 1.0, 0.0
)
data['Position'] = data['Signal'].diff().fillna(0) # Ensure Position starts cleanly
print("Trading signals generated.")

# --- Step 4: Backtesting Simulation ---
print("Running backtest simulation...")

# Calculate daily returns of the asset
data['Daily Return'] = data[price_col].pct_change()

# Determine holding status (Shift Signal by 1 day)
data['Holding'] = data['Signal'].shift(1).fillna(0)

# Calculate GROSS Strategy Returns (before costs)
data['Strategy Return'] = (data['Daily Return'] * data['Holding']).fillna(0)

# Identify trade days (where Position is 1 or -1)
trade_indices = data[data['Position'] != 0].index

# Subtract transaction costs ONLY on trade days
data.loc[trade_indices, 'Strategy Return'] -= transaction_cost_rate

print("Backtest simulation complete (including transaction costs).")

# --- Step 5: Calculate Sharpe Ratio ---
print("Calculating Sharpe Ratio...")

# Calculate mean daily strategy return (net of transaction costs)
mean_strategy_return = data['Strategy Return'].mean()

# Calculate mean daily EXCESS return (net strategy return - risk-free rate)
mean_excess_return = mean_strategy_return - daily_rf_rate

# Calculate standard deviation of daily strategy returns (net of transaction costs)
std_strategy_return = data['Strategy Return'].std()

# Calculate Sharpe Ratio
if std_strategy_return is not None and std_strategy_return != 0:
    sharpe_ratio = (mean_excess_return / std_strategy_return) * np.sqrt(annualization_factor)
    print(f"\n--- Backtest Results ---")
    print(f"Strategy Mean Daily Return (Net): {mean_strategy_return:.8f}")
    print(f"Strategy Std Dev Daily Return (Net): {std_strategy_return:.8f}")
    print(f"Mean Daily Excess Return (vs Rf): {mean_excess_return:.8f}")
    print(f"Annualized Sharpe Ratio: {sharpe_ratio:.4f}")
    print(f"------------------------")
else:
    sharpe_ratio = np.nan
    print("\n--- Backtest Results ---")
    print("Strategy standard deviation is zero or None. Cannot calculate Sharpe Ratio.")
    print(f"------------------------")


# --- Step 6: Plotting the Results ---
print("\nPlotting results...")
plt.style.use('seaborn-v0_8-darkgrid')
fig, ax = plt.subplots(figsize=(14, 7))

# Plot closing price
ax.plot(data.index, data[price_col], label=f'{ticker} Close Price', color='skyblue', linewidth=1.5, alpha=0.8)

# Plot Short and Long SMAs
ax.plot(data.index, data[f'SMA_{short_window}'], label=f'{short_window}-Day SMA', color='orange', linewidth=1.5, linestyle='--')
ax.plot(data.index, data[f'SMA_{long_window}'], label=f'{long_window}-Day SMA', color='purple', linewidth=1.5, linestyle='--')

# Plot Buy Signals
ax.plot(data[data['Position'] == 1].index,
        data[f'SMA_{short_window}'][data['Position'] == 1],
        '^', markersize=10, color='green', lw=0, label='Buy Signal')

# Plot Sell Signals
ax.plot(data[data['Position'] == -1].index,
        data[f'SMA_{short_window}'][data['Position'] == -1],
        'v', markersize=10, color='red', lw=0, label='Sell Signal')

# --- Plot Configuration ---
ax.set_title(f'{ticker} SMA ({short_window}/{long_window}) Crossover Strategy & Signals', fontsize=16)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Price (USD)', fontsize=12)
ax.legend(loc='best', fontsize=10)
ax.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

print("Plot displayed. Script finished.")