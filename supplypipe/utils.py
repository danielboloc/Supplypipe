import re, os
from datetime import timedelta, date, datetime

def str2list(string):
    # remove multiple whitespaces to just leave one
    return string.replace(",", " ").split()

def list2str(l):
    return " ".join(" ".join(l).replace(",", " ").split())

def calculate_download_days(days=729):
    """Since we are dependent of 1h time, we can only retrieve
    up to 730 prior days. Putting 729 to avoid some weird calendar
    missing day.

    The calculation is to get the day of the run - Xdays = 729
    """
    end_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    start_date = (date.today() - timedelta(days=days)).strftime('%Y-%m-%d')

    return start_date, end_date

def determine_period(date, intervals):

    start_date, end_date = calculate_download_days()
    # means we have to get 'max' data, not just 730
    if 'd' in intervals and 'w' in intervals:
        # is the date from 729 days ago, but should be changed to 'max' capacity
        if date == start_date:
            return '1998-01-01'
        # the user inputed a diff date, than the one 729 days ago, use the input
        else:
            return date
    # the interval is intrady, so we stick to 729 days from 'today'
    else:
        return date

def check_if_folder_exists(timeframe):
    today = date.today().strftime("%Y_%m_%d")
    if not os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), f"../analysis/{today}/{timeframe}"))):
        os.makedirs(os.path.abspath(os.path.join(os.path.dirname(__file__), f"../analysis/{today}/{timeframe}")))

    return os.path.abspath(os.path.join(os.path.dirname(__file__), f"../analysis/{today}/{timeframe}"))

def bid_ask_spread(ticker):
    should_skip_ticker = False
    for day in ticker.options:
        d0 = datetime.strptime(date.today().strftime("%Y-%m-%d"), '%Y-%m-%d')
        d1 = datetime.strptime(day, '%Y-%m-%d')
        delta = d1 - d0
        if delta.days > 40:
            opt = ticker.option_chain(day)
            calls = opt.calls
            OTM = calls[ calls['inTheMoney']==False ][['bid','ask']].reset_index(drop=True)
            try:
                ask = OTM.loc[0][1]
                bid = OTM.loc[0][0]
                if (ask/bid) >= 2:
                    print(f"{ticker.info['symbol']} ATM ask({ask}) is > 2 times the bid({bid}), is a different timezone, and data is closed?")
                    should_skip_ticker = True
            except (RuntimeWarning, KeyError):
                print(f"{ticker.info['symbol']} ATM bid or ask is missing")
                continue
            break
    return should_skip_ticker
