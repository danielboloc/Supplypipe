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
    SIGNALS[today]["BUY"]["1D"] = []
    SIGNALS[today]["SELL"] = {}
    SIGNALS[today]["SELL"]["1D"] = []
    SIGNALS[today]["NO_OPTIONS"] = []
    SIGNALS[today]["NO_TODAY_DATA"] = []
    SIGNALS[today]["ATM_HUGE_SPREAD"] = []
    for security in securities2download.replace(","," ").split():

        if journal_entry or monthly_report:
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

    if not journal_entry or not monthly_report:
        print(f"SIGNALS for {today}: \n")
        print(f"NO_OPTIONS:\n")
        print(f"\t\t{SIGNALS[today]['NO_OPTIONS']}: \n")
        print(f"NO_TODAY_DATA:\n")
        print(f"\t\t{SIGNALS[today]['NO_TODAY_DATA']}: \n")
        # print(f"ATM_HUGE_SPREAD:\n")
        # print(f"\t\t{SIGNALS[today]['ATM_HUGE_SPREAD']}: \n")
        print(f"BUY:\n")
        print(f"\t\t1D:\n %s\n" % [ f'{str(datetime.now().timestamp()).replace(".","")}: {s}' for s in SIGNALS[today]['BUY']['1D'] ])
        print(f"SELL:\n")
        print(f"\t\t1D:\n %s\n" % [ f'{str(datetime.now().timestamp()).replace(".","")}: {s}' for s in SIGNALS[today]['SELL']['1D'] ])

    if os.path.exists(picklename):
        backupname = picklename + '.bak'
        if os.path.exists(backupname):
            os.remove(backupname)
        os.rename(picklename, backupname)
    # save
    with open(picklename, "wb") as f:
        pickle.dump(SIGNALS, f, pickle.HIGHEST_PROTOCOL)

    def sl_tp_helper(timeframe, name, _open):
        if timeframe.lower() == '4h' and name.lower() == 'nq':
            # means we use NQ @ 4H, so the SL is ~125, TP ~250
            return round(((_open-125)),2), round(((_open+250)),2)
        elif timeframe.lower() == '1d' and name.lower() == 'nq':
            # means we use NQ @ 1D, so the SL is ~250, TP ~500
            return round(((_open-250)),2), round(((_open+500)),2)
        else:
            # means we use options, and we want open/2
            return round(((_open/2)),2), round(((_open*2)),2)


    log_into_journal = input("Would you like me to log some trades into the JOURNAL, Sir? [y/n]")
    journal_data = []
    if log_into_journal == 'y' or journal_entry:
        while True:
            print("Input 'ID','NAME','DATE_O','OPEN','EXPIRATION','STRIKE','SIZE','TYPE[C/P]','TIMEFRAME','COMM_O','PLANNED_SL','PLANNED_TP','PLANNED_RR','MISTAKES_O','MARKET_COND_O'\n\n")
            _id = int(input("ID: "))
            name = input("NAME: ")
            _open = float(input("OPEN: "))
            exp = input("EXPIRATION[YYYY-MM-DD]: ")
            strike = int(input("STRIKE: "))
            size = float(input("SIZE(1 default): ") or "1")
            type_c_p = input("TYPE[C/P]: ") # calls or puts or BUY(C) or SELL (P)
            tmfr = input("TIMEFRAME: ")
            o_comm = float(input("COMMISSION: ")) # open commision
            planned_sl, planned_tp = sl_tp_helper(tmfr, name, _open) # using loss*1:reward*2, rounding 2
            planned_rrr = round((planned_tp/planned_sl),2)
            mistakes_o = input("MISTAKES_O: ")
            market_cond_o = input("MARKET_COND_O: ")
            journal_data.append([_id,
                                 name,
                                 # if manually adding, should not automatically set to today
                                 today if not journal_entry else input("DATE_O[YYYY-MM-DD]: "),
                                 _open,
                                 exp,
                                 strike,
                                 size,
                                 type_c_p,
                                 tmfr,
                                 o_comm,
                                 planned_sl,
                                 planned_tp,
                                 planned_rrr,
                                 mistakes_o,
                                 market_cond_o]+[None]*9)
            quit = input("Press 'quit' if you are done, or return to continue, Sir: ")
            if quit == 'quit':
                print("This should suffice for today, Sir. See you tomorrow")
                break
    else:
        print("Very well, Sir. Better luck next time.")

    entries = pd.DataFrame(journal_data, columns=['ID','NAME','DATE_O','OPEN','EXP','STRIKE','SIZE','TYPE[C/P]','TIMEFRAME','COMM_O','PLANNED_SL','PLANNED_TP','PLANNED_RR','MISTAKES_O','MARKET_COND_O','DATE_C','CLOSE','C-O','REAL_RR','COMM_C','%CAUGHT','MISTAKES_C','MARKET_COND_C','P&L','TOTAL'])

    journal_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "journal"))
    journal_name = os.path.join(journal_dir, 'trade_journal.txt')

    if os.path.exists(journal_name):
        df = pd.concat([pd.read_csv(journal_name, header=0, sep=";"), entries])
    else:
        df = entries
    # CHECK OPEN positions

    # Optional to close some positions
    log_close_journal = input("Would you like me to CLOSE some trades into the JOURNAL, Sir? [y/n]")
    if log_close_journal == 'y' or journal_close:
        journal_data = []
        df["ID"] = df["ID"].astype(int) # convert to int
        df = df.set_index("ID") # set as index for easier access
        # print to master the id, name of all open positions (where DATE_C is NA)
        print('These are the current open positions:')
        print('ID\tNAME\tDATE_O\tOPEN')
        print("\n".join([f"{id}: {df.loc[id,'NAME']}\t{df.loc[id,'DATE_O']}\t{df.loc[id,'OPEN']}" for id in df[ df["DATE_C"].isnull() ].index.tolist() ]))
        while True:
            id2close = intput("WHAT ID should I close?: ")
            df.loc[id2close,'DATE_C'] = input("DATE_C[YYYY-MM-DD]: ")
            df.loc[id2close,'CLOSE'] = float(input("CLOSE: "))
            df.loc[id2close,'C-O'] = df.loc[id2close,'CLOSE'] - df.loc[id2close,'OPEN']
            df.loc[id2close,'REAL_RR'] = round((df.loc[id2close,'CLOSE']/df.loc[id2close,'PLANNED_SL']),2)
            df.loc[id2close,'COMM_C'] = float(input("COMM_C: "))
            df.loc[id2close,'%CAUGHT'] = float(input("%CAUGHT: "))
            df.loc[id2close,'MISTAKES_C'] = input("MISTAKES_C: ")
            df.loc[id2close,'MARKET_COND_C'] = input("MARKET_COND_C: ")
            df.loc[id2close,'P&L'] = float(input("P&L: "))
            df.loc[id2close,'TOTAL'] = df.loc[id2close,'P&L'] - df.loc[id2close,'COMM_C'] - df.loc[id2close,'COMM_O']
            quit = input("Press 'quit' if you are done, or return to continue, Sir: ")
            if quit == 'quit':
                print("This should suffice for today, Sir. See you tomorrow")
                break
    else:
        print("Very well, Sir. Better luck next time.")

    if os.path.exists(journal_name):
        backupname = journal_name + '.bak'
        if os.path.exists(backupname):
            os.remove(backupname)
        os.rename(journal_name, backupname)
    # save
    df.to_csv(journal_name, index=False, sep=";")

    if monthly_report:
        df = pd.read_csv(journal_name, header=0, sep=";")
        df["DATE_O"]=pd.to_datetime(df['DATE_O'])
        slicer = df.loc[(df['DATE_O'].dt.month == monthly_report)]
        nq = df.loc[(df["NAME"] == 'NQ')]
        options = df.loc[~(df["NAME"] == 'NQ')] # all except NQ
        month_day_start = f"{datetime.today().year}-0{monthly_report}-01"
        month_day_end = f'{(pd.to_datetime(month_day_start, format="%Y-%m-%d") + MonthEnd(1)).strftime("%Y-%m-%d")}'
        total_trading_days = len(pd.date_range(month_day_start, month_day_end, freq=BDay()))
        # = len(df["DATE_O"].unique().tolist())
        winning_days = len(slicer[slicer["TOTAL"]>=0]["DATE_O"].unique())
        losing_days = len(slicer[slicer["TOTAL"]<0]["DATE_O"].unique())
        #avg_winning_days
        #avg_losing_days
        total_trades = len(slicer.index)
        winning_trades = len(slicer[slicer["TOTAL"]>=0])
        losing_trades = len(slicer[slicer["TOTAL"]<0])
        avg_winning_trades = slicer[slicer["TOTAL"]>=0]["TOTAL"].mean()
        avg_losing_trades = slicer[slicer["TOTAL"]<0]["TOTAL"].mean()
        planned_rrr = slicer["PLANNED_RR"].mean()
        realized_rrr = slicer["REAL_RR"].mean()
        max_gain = slicer["TOTAL"].max()
        max_loss = slicer["TOTAL"].min()
        mistakes_o = slicer["MISTAKES_O"].dropna(how='all').values.flatten().tolist()
        mistakes_c = slicer["MISTAKES_C"].dropna(how='all').values.flatten().tolist()
        market_cond_o = slicer["MARKET_COND_O"].dropna(how='all').values.flatten().tolist()
        market_cond_c = slicer["MARKET_COND_C"].dropna(how='all').values.flatten().tolist()
        avg_size = slicer["SIZE"].mean()
        avg_winning_size = slicer[slicer["TOTAL"]>=0]["SIZE"].mean()
        avg_losing_size = slicer[slicer["TOTAL"]<0]["SIZE"].mean()
        total_month = slicer["TOTAL"].sum()
        print(f"REPORT for YEAR {datetime.today().year}, MONTH {monthly_report}: ")
        print(f"total_trading_days: {total_trading_days}")
        print(f"winning_days: {winning_days}")
        print(f"losing_days: {losing_days}")
        print(f"total_trades: {total_trades}")
        print(f"winning_trades: {winning_trades}")
        print(f"losing_trades: {losing_trades}")
        print(f"avg_winning_trades: {avg_winning_trades}")
        print(f"avg_losing_trades: {avg_losing_trades}")
        print(f"planned_rrr: {planned_rrr}")
        print(f"realized_rrr: {realized_rrr}")
        print(f"max_gain: {max_gain}")
        print(f"max_loss: {max_loss}")
        print(f"mistakes opening: {mistakes_o}")
        print(f"mistakes closing: {mistakes_c}")
        print(f"market condition open: {market_cond_o}")
        print(f"market condition close: {market_cond_c}")
        print(f"avg_size: {avg_size}")
        print(f"avg_winning_size: {avg_winning_size}")
        print(f"avg_losing_size: {avg_losing_size}")
        print(f"total month: {total_month}")
        # separate NQ

        # the rest are options

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