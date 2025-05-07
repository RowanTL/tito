#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  7 12:48:54 2025

@author: rowan
"""

import polars as pl
from typing import Optional
from os import PathLike

def prune_time(timeframe: int, timestep: str = "hourly", df: Optional[pl.DataFrame] = None, csv_path: Optional[str | PathLike] = None) -> pl.DataFrame:
    """
    Takes in a dataframe or a path to a csv file to read in as a dataframe and splits
    removes data that doesn't fit into the specified timeframe for a given timestep.
    
    For example:
        prune_time(6, timestep="hourly", df=arbitrary_df) would return a new dataframe
        where the passed dataframe had all its hours not divisible by 6 removed.
        If hourly were say "daily", it would be every six days instead.
        
    parameters:
        timeframe (int): The time frame to keep in the data.
        timestep (str, default = "hourly"): Respective to the data passed in.
            Lets the internal polars call know which time related function to use.
            Options: "hourly", "daily"
        df (Optional[pl.DataFrame], default = None): The data frame to perform the pruning on.
            Can't be used with csv_path.
        csv_path (optional[str | PathLike], default = None): Path to a csv file to
            read and then perform the operations on. Can't be used with df.
    """
    if df is None and csv_path is None:
        print("Must provide either a df or a path to a csv file, got None for both!")
        exit(1)
    if df is not None and csv_path is not None:
        print("Passed values to both df and csv_path! Can't do that!")
        exit(1)
    final_df = df
    if csv_path is not None:
        final_df = pl.read_csv(csv_path, try_parse_dates=True)
        
    match timestep:
        case "hourly":
            filtered_df: pl.DataFrame = final_df.filter(pl.col("Datetime").dt.hour() % timeframe == 0)
        case "daily":
            filtered_df: pl.DataFrame = final_df.filter(pl.col("Datetime").dt.day() % timeframe == 0)
        case _:
            print(f"Error: timestep for {timestep} not implemented!")
            exit(1)
            
    return filtered_df

if __name__ == "__main__":
    timestep = 12
    timespan: str = "6mo"
    df = prune_time(timestep, "hourly", csv_path=f"btc_data/hourly_{timespan}.csv")
    df.write_csv(f"btc_data/hourly_{timestep}_{timespan}.csv")