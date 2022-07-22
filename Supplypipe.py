#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import click
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supplypipe.studies import oneDay_oneWeek
from datetime import timedelta, date, datetime
from supplypipe.config import get_configuration
from supplypipe.utils import list2str, calculate_download_days, determine_period

# Setup days for the data retrieval, since we only get 730D @1h
start_date, end_date = calculate_download_days()

@click.command()
@click.option("--only-stock",
              is_flag=True,
              help="To only look at the 'stocks' section in config")
@click.option("--on-demand",
              help="""You can put the ticker symbol, e.g MSFT or multiple 'MSFT,
                      AAPL'""")
@click.option("--intervals",
              help="Three intervals for multi-timeframe analysis",
              default='60m 1d 1wk')
@click.option("--start",
              help="""Start date of data retrieval. The analysis will be
                      performed in this interval also""",
              default=start_date) # 729 previous days
@click.option("--end",
              help="End date of data retrieval",
              default=end_date) # today
def main(only_stock, on_demand, intervals, start, end):

    # Setup configuration files
    config = get_configuration()

    # Look at only 'STOCKS' section in the config
    if only_stock:
        securities2download = config["SECTORS"]["stocks"]
    # Only apply the study for the command-line argument/s passed
    elif on_demand:
        securities2download = on_demand
    # Apply the study to all sectors in the config
    else:
        securities2download = list2str(list(config["SECTORS"].values())) # str

    # Loop over the securities and apply the study/s
    for security in securities2download.replace(","," ").split():
        # run study/strategy
        oneDay_oneWeek(security, intervals, on_demand)

if __name__ == '__main__':
    main()

