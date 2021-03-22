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
@click.option("--journal-entry",
              help="Manual entry of trades",
              is_flag=True)
@click.option("--journal-close",
              help="Manual closing of trades",
              is_flag=True)
@click.option("--journal-sizing",
              help="Manual size in/out of trades (which are already logged)",
              is_flag=True)
def main(only_stock, on_demand, intervals, start, end, journal_entry, journal_close, journal_sizing):
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
    weekday = datetime.today().weekday() # returns a number: 5,6->Sat,Sun
    # if running on a weekend, will consider as friday
    if 5 <= weekday >= 6:
        today = (date.today() - BDay(1)).strftime("%Y-%m-%d")
        yesterday = (date.today() - BDay(2)).strftime("%Y-%m-%d")
    else:
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
    SIGNALS[today]["ATM_HUGE_SPREAD"] = []
    for security in securities2download.replace(","," ").split():

        if journal_entry:
            break

        ticker = yf.Ticker(security)

        if not on_demand:
            try:
                ticker.options
            except IndexError:
                SIGNALS[today]["NO_OPTIONS"].append(security)
                print(f"{security} does not have options, skipping...")
                continue
            # else:
            #     if bid_ask_spread(ticker): # determine if I should skip this ticker
            #         SIGNALS[today]["ATM_HUGE_SPREAD"].append(security)
            #         continue

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

            buy_fourH_oneD = exp7.loc[today].tail(-1)[0] > exp21.loc[today].tail(-1)[0] and exp7.loc[yesterday].tail(-1)[0] < exp21.loc[yesterday].tail(-1)[0]
            sell_fourH_oneD = exp7.loc[today].tail(-1)[0] < exp21.loc[today].tail(-1)[0] and exp7.loc[yesterday].tail(-1)[0] > exp21.loc[yesterday].tail(-1)[0]
            buy_oneD_oneW = exp3.loc[today] > exp15.loc[today] and exp3.loc[yesterday] < exp15.loc[yesterday] and exp5.loc[today] > exp15_w.loc[today]
            sell_oneD_oneW = exp3.loc[today] < exp15.loc[today] and exp3.loc[yesterday] > exp15.loc[yesterday] and exp5.loc[today] < exp15_w.loc[today]
            # make sure both the 1d and 1w are up, not looking for 1D cross
            buy_zone_day_week = exp3.loc[today] > exp15.loc[today] and exp5.loc[today] > exp15_w.loc[today]
            # make sure both the 1d and 1w are down, not looking for 1D cross
            sell_zone_day_week = exp3.loc[today] < exp15.loc[today] and exp5.loc[today] < exp15_w.loc[today]

            if on_demand:
                mtf(security,check_if_folder_exists("on_demand"),hour4,day,week,exp3,exp5,exp7,exp15,exp15_w,exp21)
            # Discontinued 4H buying and selling
            # elif buy_fourH_oneD and buy_zone_day_week:
            #     # BUY signal
            #     mtf(security,
            #         check_if_folder_exists("4H/BUY"),
            #         hour4,
            #         day,
            #         week,
            #         exp3,
            #         exp5,
            #         exp7,
            #         exp15,
            #         exp15_w,
            #         exp21)
            #     if security not in SIGNALS[today]["BUY"]["4H"]: SIGNALS[today]["BUY"]["4H"].append(security)
            #     #draw()
            # elif sell_fourH_oneD and sell_zone_day_week:
            #     # SELL signal
            #     mtf(security,
            #         check_if_folder_exists("4H/SELL"),
            #         hour4,
            #         day,
            #         week,
            #         exp3,
            #         exp5,
            #         exp7,
            #         exp15,
            #         exp15_w,
            #         exp21)
            #     if security not in SIGNALS[today]["SELL"]["4H"]: SIGNALS[today]["SELL"]["4H"].append(security)
            #     #check_if_folder_exists("4H")
            # Check at 1D vs 1W
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
                if security not in SIGNALS[today]["BUY"]["1D"]: SIGNALS[today]["BUY"]["1D"].append(security)
                #check_if_folder_exists("1D")
                #draw()
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
                if security not in SIGNALS[today]["SELL"]["1D"]: SIGNALS[today]["SELL"]["1D"].append(security)

        except (KeyError, IndexError) as e:
            SIGNALS[today]["NO_TODAY_DATA"].append(security)
            print(f"{security} does not yet have TODAY's data, try again later")
            continue

    if not journal_entry:
        print(f"SIGNALS for {today}: \n")
        print(f"NO_OPTIONS:\n")
        print(f"\t\t{SIGNALS[today]['NO_OPTIONS']}: \n")
        print(f"NO_TODAY_DATA:\n")
        print(f"\t\t{SIGNALS[today]['NO_TODAY_DATA']}: \n")
        # print(f"ATM_HUGE_SPREAD:\n")
        # print(f"\t\t{SIGNALS[today]['ATM_HUGE_SPREAD']}: \n")
        print(f"BUY:\n")
        print("\t\t4H:\n %s\n" % [ f'{str(datetime.now().timestamp()).replace(".","")}: {s}' for s in SIGNALS[today]['BUY']['4H'] ])
        print(f"\t\t1D:\n %s\n" % [ f'{str(datetime.now().timestamp()).replace(".","")}: {s}' for s in SIGNALS[today]['BUY']['1D'] ])
        print(f"SELL:\n")
        print(f"\t\t4H:\n %s\n" % [ f'{str(datetime.now().timestamp()).replace(".","")}: {s}' for s in SIGNALS[today]['SELL']['4H'] ])
        print(f"\t\t1D:\n %s\n" % [ f'{str(datetime.now().timestamp()).replace(".","")}: {s}' for s in SIGNALS[today]['SELL']['1D'] ])

    if os.path.exists(picklename):
        backupname = picklename + '.bak'
        if os.path.exists(backupname):
            os.remove(backupname)
        os.rename(picklename, backupname)
    # save
    with open(picklename, "wb") as f:
        pickle.dump(SIGNALS, f, pickle.HIGHEST_PROTOCOL)

    log_into_journal = input("Would you like me to log some trades into the JOURNAL, Sir? [y/n]")
    journal_data = []
    if log_into_journal == 'y' or journal_entry:
        while True:
            print("Input ID, NAME, OPEN, EXPIRATION, STRIKE, TYPE[C/P], TIMEFRAME, COMMISSION\n\n")
            _id = input("ID: ")
            name = input("NAME: ")
            _open = input("OPEN: ")
            exp = input("EXPIRATION[YYYY-MM-DD]: ")
            strike = input("STRIKE: ")
            type_c_p = input("TYPE[C/P]: ") # calls or puts
            tmfr = input("TIMEFRAME: ")
            o_comm = input("COMMISSION: ") # open commision
            journal_data.append([_id,
                                 name,
                                 # if manually adding, should not automatically set to today
                                 today if not journal_entry else input("DATE_O[YYYY-MM-DD]: "),
                                 _open,
                                 exp,
                                 strike,
                                 type_c_p,
                                 tmfr,
                                 o_comm]+[None]*7)
            quit = input("Press 'quit' if you are done, or return to continue, Sir: ")
            if quit == 'quit':
                print("This should suffice for today, Sir. See you tomorrow")
                break
    else:
        print("Very well, Sir. Better luck next time.")

    entries = pd.DataFrame(journal_data, columns=['ID','NAME','DATE_O','OPEN','EXPIRATION','STRIKE','TYPE[C/P]','TIMEFRAME','COMM_O','DATE_C','CLOSE','C-O','R:R','%CAUGHT','P&L','TOTAL'])

    journal_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "journal"))
    journal_name = os.path.join(journal_dir, 'trade_journal.txt')

    if os.path.exists(journal_name):
        df = pd.concat([pd.read_csv(journal_name, header=0), entries])
    else:
        df = entries

    # CHECK OPEN positions

    # Optional to close some positions

    if os.path.exists(journal_name):
        backupname = journal_name + '.bak'
        if os.path.exists(backupname):
            os.remove(backupname)
        os.rename(journal_name, backupname)
    # save
    df.to_csv(journal_name, index=False)

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