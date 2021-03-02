from supplypipe.config import get_configuration
from supplypipe.utils import list2str, calculate_download_days, determine_period
from supplypipe.utils import check_if_folder_exists
from supplypipe.downloader import download
from supplypipe.plots import mtf
import yfinance as yf
import click
import plotly.graph_objects as go
import pandas as pd
from datetime import timedelta, date
from pandas.tseries.offsets import BDay # business days
import pickle
import os

# Setup days for the data retrieval, since we only get 730D @1h
start_date, end_date = calculate_download_days()

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
def main(only_stock, on_demand, intervals, start, end):
    config = get_configuration()
    # tickers = yf.Tickers(config["SECTORS"]["technology"])
    # print(tickers.tickers.QQQ.history(period="1mo"))
    # print(tickers.tickers.QQQ.major_holders)
    if only_stock:
        securities2download = config["STOCKS"]["securities"] # str
    elif on_demand:
        securities2download = on_demand # str
    else:
        securities2download = list2str(list(config["SECTORS"].values())) # str

    # prepare options for API
    # options = {'start': determine_period(start, intervals),
    #            'end': determine_period(end, intervals)}

    #hour, day, week = download(securities2download, intervals, **options)
    today = date.today().strftime("%Y-%m-%d")
    yesterday = (date.today() - BDay(1)).strftime("%Y-%m-%d")

    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "history"))
    picklename = os.path.join(directory, 'supply_trades.pickle')

    if os.path.exists(picklename):
        with open(picklename, 'rb') as f:
            SIGNALS = pickle.load(f)
    else:
        SIGNALS = dict()

    SIGNALS[today] = {}
    SIGNALS[today]["BUY"] = {}
    SIGNALS[today]["BUY"]["4H"] = []
    SIGNALS[today]["BUY"]["1D"] = []
    SIGNALS[today]["SELL"] = {}
    SIGNALS[today]["SELL"]["4H"] = []
    SIGNALS[today]["SELL"]["1D"] = []
    SIGNALS[today]["NO_OPTIONS"] = []
    SIGNALS[today]["NO_TODAY_DATA"] = []
    for security in securities2download.replace(","," ").split():

        ticker = yf.Ticker(security)

        try:
            ticker.options
        except IndexError:
            SIGNALS[today]["NO_OPTIONS"].append(security)
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
        # from scipy import stats
        # import numpy as np
        # hour4 = hour4[(np.abs(stats.zscore(hour4)) < 3).all(axis=1)]
        #hour42 = hour.resample('4H').mean().dropna()
        oneD = hour.resample('B').mean() # business day
        # plot data with EMAs
            # if is too large split by year

        exp3 = day['Close'].ewm(span=3, adjust=True).mean()
        exp5 = week['Close'].ewm(span=5, adjust=True).mean()
        exp7 = hour4['Close'].ewm(span=7, adjust=True).mean()
        exp15 = day['Close'].ewm(span=15, adjust=True).mean()
        exp15_w = week['Close'].ewm(span=15, adjust=True).mean()
        exp21 = hour4['Close'].ewm(span=21, adjust=True).mean()

        # only business day
        # Check at 4h vs 1D
        try:
            if exp7.loc[today].tail(-1)[0] > exp21.loc[today].tail(-1)[0] and exp7.loc[yesterday].tail(-1)[0] < exp21.loc[yesterday].tail(-1)[0] and exp3.loc[today] > exp15.loc[today]:
                # BUY signal
                mtf(security,
                    check_if_folder_exists("4H"),
                    hour4,
                    day,
                    week,
                    exp3,
                    exp5,
                    exp7,
                    exp15,
                    exp15_w,
                    exp21)
                if security not in SIGNALS[today]["BUY"]["4H"]: SIGNALS[today]["BUY"]["4H"].append(security)
                #draw()
            elif exp7.loc[today].tail(-1)[0] < exp21.loc[today].tail(-1)[0] and exp7.loc[yesterday].tail(-1)[0] > exp21.loc[yesterday].tail(-1)[0] and exp3.loc[today] < exp15.loc[today]:
                # SELL signal
                mtf(security,
                    check_if_folder_exists("4H"),
                    hour4,
                    day,
                    week,
                    exp3,
                    exp5,
                    exp7,
                    exp15,
                    exp15_w,
                    exp21)
                if security not in SIGNALS[today]["SELL"]["4H"]: SIGNALS[today]["SELL"]["4H"].append(security)
                #check_if_folder_exists("4H")
            # Check at 1D vs 1W
            elif exp3.loc[today] > exp15.loc[today] and exp3.loc[yesterday] < exp15.loc[yesterday] and exp5.loc[today] > exp15_w.loc[today]:
                # BUY signal
                mtf(security,
                    check_if_folder_exists("1D"),
                    hour4,
                    day,
                    week,
                    exp3,
                    exp5,
                    exp7,
                    exp15,
                    exp15_w,
                    exp21)
                if security not in SIGNALS[today]["BUY"]["1D"]: SIGNALS[today]["BUY"]["1D"].append(security)
                #check_if_folder_exists("1D")
                #draw()
            elif exp3.loc[today] < exp15.loc[today] and exp3.loc[yesterday] > exp15.loc[yesterday] and exp5.loc[today] < exp15_w.loc[today]:
                # SELL signal
                mtf(security,
                    check_if_folder_exists("1D"),
                    hour4,
                    day,
                    week,
                    exp3,
                    exp5,
                    exp7,
                    exp15,
                    exp15_w,
                    exp21)
                if security not in SIGNALS[today]["SELL"]["1D"]: SIGNALS[today]["SELL"]["1D"].append(security)
                #check_if_folder_exists("1D")
        except (KeyError, IndexError) as e:
            SIGNALS[today]["NO_TODAY_DATA"].append(security)
            print(f"{security} does not yet have TODAY's data, try again later")
            continue

    print(f"SIGNALS for {today}: \n")
    print(f"BUY:\n")
    print(f"\t\t4H: {SIGNALS[today]['BUY']['4H']}: \n")
    print(f"\t\t1D: {SIGNALS[today]['BUY']['1D']}: \n")
    print(f"SELL:\n")
    print(f"\t\t4H: {SIGNALS[today]['SELL']['4H']}: \n")
    print(f"\t\t1D: {SIGNALS[today]['SELL']['1D']}: \n")
    print(f"NO_OPTIONS:\n")
    print(f"\t\t{SIGNALS[today]['NO_OPTIONS']}: \n")
    print(f"NO_TODAY_DATA:\n")
    print(f"\t\t{SIGNALS[today]['NO_TODAY_DATA']}: \n")

    if os.path.exists(picklename):
        backupname = picklename + '.bak'
        if os.path.exists(backupname):
            os.remove(backupname)
        os.rename(picklename, backupname)
    # save
    with open(picklename, "wb") as f:
        pickle.dump(SIGNALS, f, pickle.HIGHEST_PROTOCOL)
    #data.resample('D').mean().fillna(method='bfill')
    #mpf.plot(greatTime)
    #print(exp7)
    #print(exp21)

    # multi-time analysis
        # 4h-1D; 4h-1W; 4h-1D-1W
        # price range for what price movement you can expect
        # How long you should hold
        # What combination of EMAs & timeframes is the best for profits
        # option study or movement in underlying with premium
        # Provide trade scoring system
        # buy 1D, 1W at each cross

    # signals

    # journal
        # insert manually
        # accept ID of proposed positions

    # Alerts, logs, confirmation for positions

    # monthly reports
        # Add profits & days held
        # Divide by year, all, custom time   

        # for security in config["SECTORS"][sector].split(", "):
        #     df = data[security]
        #     fig = go.Figure(data=[go.Candlestick(x=df.loc['2021-01-01':'2021-02-18'],
        #                     open=df['Open'],
        #                     high=df['High'],
        #                     low=df['Low'],
        #                     close=df['Close'])])

        #     fig.show()

if __name__ == '__main__':
    main()