#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Implementation of MACD with polars and scikit-learn grid search

import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from math import sqrt
from pathlib import Path
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.base import BaseEstimator, RegressorMixin
import pandas as pd


class MACDStrategy(BaseEstimator, RegressorMixin):
    """
    MACD trading strategy implemented as a scikit-learn compatible estimator.
    This enables grid search for parameter optimization.
    """
    
    def __init__(self, short_span=12, long_span=26, signal_span=9, transaction_cost=0.0005, 
                 risk_free_rate=0.0421, trading_days=1461):
        self.short_span = short_span
        self.long_span = long_span
        self.signal_span = signal_span
        self.transaction_cost = transaction_cost
        self.risk_free_rate = risk_free_rate
        self.trading_days = trading_days
        
    def fit(self, X, y=None):
        """
        Fits the MACD strategy to price data.
        
        Parameters:
        -----------
        X : polars.DataFrame or pandas.DataFrame
            DataFrame with price data. Must contain 'Close' column.
        y : None
            Not used, present for API consistency
            
        Returns:
        --------
        self : object
            Returns self
        """
        # Convert pandas to polars if needed
        if isinstance(X, pd.DataFrame):
            data = pl.from_pandas(X)
        else:
            data = X.clone()
            
        col_name = "Close"
        
        # Calculate MACD components
        data = data.with_columns((pl.col(col_name).ewm_mean(span=self.short_span)).alias(f"{col_name}_ewm_{self.short_span}"))
        data = data.with_columns((pl.col(col_name).ewm_mean(span=self.long_span)).alias(f"{col_name}_ewm_{self.long_span}"))
        data = data.with_columns((pl.col(f"{col_name}_ewm_{self.short_span}") - pl.col(f"{col_name}_ewm_{self.long_span}")).alias("MACD_line"))
        data = data.with_columns(pl.col("MACD_line").ewm_mean(span=self.signal_span).alias("signal_line"))

        # Calculate histogram values (MACD line - signal line)
        data = data.with_columns((pl.col("MACD_line") - pl.col("signal_line")).alias("histogram"))

        # Introduce signals
        positions = data.select(pl.when(pl.col("MACD_line") > pl.col("signal_line"))
                                .then(1)
                                .otherwise(0)
                                .alias("positions")).to_series()

        dailyret = data.select((pl.col(col_name).pct_change()).alias("dailyret")).to_series()
        excessret = dailyret - self.risk_free_rate / self.trading_days
        
        # Profit and loss
        pnl_per = positions.shift() * excessret
        all_transaction_costs = abs(pnl_per) * self.transaction_cost
        # Profit and loss with transaction costs
        pnl_t = (pnl_per - all_transaction_costs)
        
        # Store results
        self.total_pnl_ = pnl_t.sum()
        self.pnl_t_ = pnl_t
        self.data_ = data
        
        # Calculate Sharpe ratio
        valid_pnl = pnl_t[1:]  # Skip first NaN entry
        if len(valid_pnl) > 0 and valid_pnl.std() > 0:
            self.sharpe_ratio_ = sqrt(self.trading_days) * valid_pnl.mean() / valid_pnl.std()
        else:
            self.sharpe_ratio_ = -np.inf  # Penalize invalid combinations
            
        return self
    
    def predict(self, X):
        """
        Not actually used for prediction, just returns the Sharpe ratio.
        Needed for scikit-learn compatibility.
        """
        return np.ones(len(X)) * self.sharpe_ratio_
    
    def score(self, X, y=None):
        """
        Returns the Sharpe ratio as the score.
        Higher is better.
        """
        return self.sharpe_ratio_


def plot_macd_results(data, col_name="Close", title_timespan=""):
    """
    Plot the price and MACD indicators
    """
    # Convert to pandas for plotting
    plot_df = data.to_pandas() if isinstance(data, pl.DataFrame) else data
    
    # Create plot with 2 subplots - price on top, MACD with histogram below
    plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])

    # Price chart
    ax1 = plt.subplot(gs[0])
    ax1.plot(plot_df["Datetime"], plot_df[col_name], label="Bitcoin Price", color="black")
    ax1.set_title(f"Bitcoin Price ({title_timespan})")
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


def plot_grid_search_results(grid_search, param_name, score_name='mean_test_score'):
    """
    Plot grid search results for a specific parameter
    """
    results = pd.DataFrame(grid_search.cv_results_)
    
    # Group by the parameter and calculate mean score
    param_scores = results.groupby(f'param_{param_name}')[score_name].mean()
    
    plt.figure(figsize=(10, 6))
    plt.plot(param_scores.index, param_scores.values, marker='o')
    plt.title(f'Grid Search Results: Impact of {param_name} on Sharpe Ratio')
    plt.xlabel(param_name)
    plt.ylabel('Mean Sharpe Ratio')
    plt.grid(True)
    plt.show()


def main():
    # Load data
    timespan: str = "6mo"
    df_path: Path = Path(f"../../data/btc_data/hourly_6_{timespan}.csv")
    data = pl.read_csv(df_path)
    
    # Configuration
    transaction_cost = 0.0005
    risk_free_rate = 0.0421
    trading_days = 1461  # For 6-hour increments
    
    # Define parameter grid
    param_grid = {
        'short_span': list(range(3, 50, 1)),     # 5, 10, 15, 20, 25
        'long_span': list(range(10, 101, 1)),    # 20, 30, 40, 50
        'signal_span': list(range(2, 30, 1))     # 3, 6, 9, 12, 15
    }
    
    # Create the model
    base_macd_model = MACDStrategy(
        transaction_cost=transaction_cost,
        risk_free_rate=risk_free_rate,
        trading_days=trading_days
    )
    
    # Manual grid search implementation without validation
    best_params = {}
    best_sharpe = -np.inf
    results = []
    
    # Print header
    print(f"{'short_span':<10} {'long_span':<10} {'signal_span':<10} {'Sharpe Ratio':<15}")
    print("-" * 50)
    
    # Iterate through all parameter combinations
    for short_span in param_grid['short_span']:
        for long_span in param_grid['long_span']:
            # Skip invalid combinations where short_span >= long_span
            if short_span >= long_span:
                continue
                
            for signal_span in param_grid['signal_span']:
                # Create a new model with current parameters
                model = MACDStrategy(
                    short_span=short_span,
                    long_span=long_span,
                    signal_span=signal_span,
                    transaction_cost=transaction_cost,
                    risk_free_rate=risk_free_rate,
                    trading_days=trading_days
                )
                
                # Fit model on entire dataset
                model.fit(data)
                sharpe = model.sharpe_ratio_
                
                # Store results
                result = {
                    'param_short_span': short_span,
                    'param_long_span': long_span,
                    'param_signal_span': signal_span,
                    'mean_test_score': sharpe  # Using this field for compatibility with plotting functions
                }
                results.append(result)
                
                # Print current result
                print(f"{short_span:<10} {long_span:<10} {signal_span:<10} {sharpe:<15.4f}")
                
                # Update best params if current is better
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = {
                        'short_span': short_span,
                        'long_span': long_span,
                        'signal_span': signal_span
                    }
                    best_model = model
    
    # Convert results to DataFrame for easier analysis
    results_df = pd.DataFrame(results)
    
    # Create a GridSearchCV-like results structure for compatibility with plotting functions
    class GridSearchResults:
        def __init__(self, cv_results, best_params, best_score, best_estimator):
            self.cv_results_ = cv_results
            self.best_params_ = best_params
            self.best_score_ = best_score
            self.best_estimator_ = best_estimator
    
    grid_search = GridSearchResults(
        cv_results=results,
        best_params=best_params,
        best_score=best_sharpe,
        best_estimator=best_model
    )
    
    # Print best parameters and results
    print("Best parameters:", grid_search.best_params_)
    print("Best Sharpe ratio:", grid_search.best_score_)
    
    # Get the best model
    best_model = grid_search.best_estimator_
    
    # Plot parameter impact
    plot_grid_search_results(grid_search, 'short_span')
    plot_grid_search_results(grid_search, 'long_span')
    plot_grid_search_results(grid_search, 'signal_span')
    
    # Plot final MACD results with best parameters
    print(f"Plotting MACD with best parameters: short_span={best_model.short_span}, "
          f"long_span={best_model.long_span}, signal_span={best_model.signal_span}")
    plot_macd_results(best_model.data_, title_timespan=timespan)
    
    # Create a heatmap for parameter combinations
    results = pd.DataFrame(grid_search.cv_results_)
    
    # Check if we have enough unique values for a meaningful heatmap
    if len(np.unique(results['param_short_span'])) > 1 and len(np.unique(results['param_signal_span'])) > 1:
        # Create pivot table for short_span vs signal_span
        pivot1 = results.pivot_table(
            index='param_short_span', 
            columns='param_signal_span', 
            values='mean_test_score',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(pivot1, annot=True, cmap='viridis', fmt='.3f')
        plt.title('Sharpe Ratio: short_span vs signal_span')
        plt.tight_layout()
        plt.show()

    if len(np.unique(results['param_short_span'])) > 1 and len(np.unique(results['param_long_span'])) > 1:
        # Create pivot table for short_span vs long_span
        pivot2 = results.pivot_table(
            index='param_short_span', 
            columns='param_long_span', 
            values='mean_test_score',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(pivot2, annot=True, cmap='viridis', fmt='.3f')
        plt.title('Sharpe Ratio: short_span vs long_span')
        plt.tight_layout()
        plt.show()
        
    if len(np.unique(results['param_long_span'])) > 1 and len(np.unique(results['param_signal_span'])) > 1:
        # Create pivot table for long_span vs signal_span
        pivot3 = results.pivot_table(
            index='param_long_span', 
            columns='param_signal_span', 
            values='mean_test_score',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(pivot3, annot=True, cmap='viridis', fmt='.3f')
        plt.title('Sharpe Ratio: long_span vs signal_span')
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    # Add missing import for seaborn
    import seaborn as sns
    main()