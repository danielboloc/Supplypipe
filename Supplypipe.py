from supplypipe.config import get_configuration
from supplypipe.utils import list2str, calculate_download_days, determine_period
from supplypipe.utils import check_if_folder_exists, bid_ask_spread
from supplypipe.downloader import download
from supplypipe.plots import mtf
import yfinance as yf
import click
import plotly.graph_objects as go
import pandas as pd
from datetime import timedelta, date, datetime
from pandas.tseries.offsets import BDay # business days
from pandas.tseries.offsets import MonthEnd
import pickle
import os

# Setup days for the data retrieval, since we only get 730D @1h
start_date, end_date = calculate_download_days()
number2month = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun',
                '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'}

@click.command()
@click.option("--only-stock",
              is_flag=True,
              help="To only look at the 'stock' section in config")
@click.option("--on-demand",
              help="You can put the ticker symbol, e.g MSFT or multiple 'MSFT, AAPL'")
@click.option("--intervals",
              help="Two intervals for multi-timeframe analysis",
              default='60m 1d 1wk')
@click.option("--start",
              help="Start date of data retrieval. The analysis will be performed in this interval also",
              default=start_date) # 729 previous days
@click.option("--end",
              help="End date of data retrieval",
              default=end_date) # today
@click.option("--journal-entry",
              help="Manual entry of trades",
              is_flag=True)
@click.option("--journal-close",
              help="Manual closing of trades",
              is_flag=True)
@click.option("--journal-sizing",
              help="Manual size in/out of trades (which are already logged)",
              is_flag=True)
@click.option("--monthly-report",
              help="Create report for the month that you put. E.g. '3'",
              type=int)
def main(only_stock,
         on_demand,
         intervals,
         start,
         end,
         journal_entry,
         journal_close,
         journal_sizing,
         monthly_report):
    config = get_configuration()
    if only_stock:
        securities2download = config["STOCKS"]["securities"] # str
    elif on_demand:
        securities2download = on_demand # str
    else:
        securities2download = list2str(list(config["SECTORS"].values())) # str

    weekday = datetime.today().weekday() # returns a number: 5,6->Sat,Sun
    # if running on a weekend, will consider as friday
    if 5 <= weekday >= 6:
        today = (date.today() - BDay(1)).strftime("%Y-%m-%d")
        yesterday = (date.today() - BDay(2)).strftime("%Y-%m-%d")
    else:
        today = date.today().strftime("%Y-%m-%d")
        yesterday = (date.today() - BDay(1)).strftime("%Y-%m-%d")

    for security in securities2download.replace(","," ").split():

        ticker = yf.Ticker(security)

        if not on_demand:
            try:
                ticker.options
            except IndexError:
                print(f"{security} does not have options, skipping...")
                continue

        print(f"Security download: {security}")
        hour, day, week = download(security, intervals)
        ohlc_dict = {                                                                                                             
            'Open':'first',                                                                                                    
            'High':'max',                                                                                                       
            'Low':'min',                                                                                                        
            'Close': 'last',                                                                                                    
            'Volume': 'sum'                                                                                                        
        }
        hour4 = hour.resample('4H').agg(ohlc_dict).dropna()
        # if using the premarket, filter outliers
        oneD = hour.resample('B').mean() # business day
        # plot data with EMAs
        exp3 = day['Close'].ewm(span=3, adjust=True).mean()
        exp5 = week['Close'].ewm(span=5, adjust=True).mean()
        exp7 = hour4['Close'].ewm(span=7, adjust=True).mean() 
        exp15 = day['Close'].ewm(span=15, adjust=True).mean()
        exp15_w = week['Close'].ewm(span=15, adjust=True).mean()
        exp21 = hour4['Close'].ewm(span=21, adjust=True).mean()

        # only business day
        # Check at 4h vs 1D
        try:
            # datetime instead of just date -> gives error
            buy_oneD_oneW = exp3.loc[today] > exp15.loc[today] and exp3.loc[yesterday] < exp15.loc[yesterday] and exp5.loc[today] > exp15_w.loc[today]
            sell_oneD_oneW = exp3.loc[today] < exp15.loc[today] and exp3.loc[yesterday] > exp15.loc[yesterday] and exp5.loc[today] < exp15_w.loc[today]
            # make sure both the 1d and 1w are up, not looking for 1D cross
            # make sure both the 1d and 1w are down, not looking for 1D cross

            if on_demand:
                mtf(security,check_if_folder_exists("on_demand"),hour4,day,week,exp3,exp5,exp7,exp15,exp15_w,exp21)
            elif buy_oneD_oneW:
                # BUY signal
                mtf(security,
                    check_if_folder_exists("1D/BUY"),
                    hour4,
                    day,
                    week,
                    exp3,
                    exp5,
                    exp7,
                    exp15,
                    exp15_w,
                    exp21)
            elif sell_oneD_oneW:
                # SELL signal
                mtf(security,
                    check_if_folder_exists("1D/SELL"),
                    hour4,
                    day,
                    week,
                    exp3,
                    exp5,
                    exp7,
                    exp15,
                    exp15_w,
                    exp21)

        except (KeyError, IndexError) as e:
            print(f"{security} does not yet have TODAY's data, try again later")
            continue

if __name__ == '__main__':
    main()

