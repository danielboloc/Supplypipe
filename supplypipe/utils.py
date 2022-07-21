# -*- coding: utf-8 -*-

import re, os
import numpy as np
from datetime import timedelta, date, datetime
from pandas.tseries.offsets import BDay # business days

def str2list(string):
    """
    Remove multiple whitespaces to just leave one and convert to list
    
    :param str string: input string

    :returns: list representation of the string
    :rtype: list
    """
    return string.replace(",", " ").split()

def list2str(l):
    """
    Convert a list's values to strings, without commas
    
    :param list l: input list

    :returns: string representation of the list
    :rtype: str
    """
    return " ".join(" ".join(l).replace(",", " ").split())

def calculate_download_days(days=729):
    """
    Since we are dependent of 1h time, we can only retrieve
    up to 730 prior days. Putting 729 to avoid some weird calendar
    missing day.

    The calculation is to get the day of the run - Xdays = 729

    :param int days: maximum number of days it will retrieve

    :return: based on the date, the start date and end date of when the data
    should be retrieved
    :rtype: tuple
    """
    end_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    start_date = (date.today() - timedelta(days=days)).strftime('%Y-%m-%d')

    return start_date, end_date

def determine_today_yesterday():
    """
    When running the analysis on the weekends, it needs to condider that the last
    day is Friday. Depending on this yesterday will be set. Since markets are
    open only Monday-Friday.

    :returns: the day representation of 'today' and 'yesterday'
    :rtype: tuple
    """

    weekday = datetime.today().weekday() # returns a number: 5,6->Sat,Sun
    # if running on a weekend, will consider as friday
    if 5 <= weekday >= 6:
        today = (date.today() - BDay(1)).strftime("%Y-%m-%d")
        yesterday = (date.today() - BDay(2)).strftime("%Y-%m-%d")
    else:
        today = date.today().strftime("%Y-%m-%d")
        yesterday = (date.today() - BDay(1)).strftime("%Y-%m-%d")

    return today, yesterday

def setup_ohlc():
    """Return a dictionary containing settings for:
        - open
        - high
        - low
        - close
        - volume
    """
    return {
        'Open':'first',
        'High':'max',
        'Low':'min',
        'Close': 'last',
        'Volume': 'sum'
    }

def determine_period(date, intervals):
    """
    Ensures that the used input is limited to a certain number of days to
    avoid errors in data retrieval

    :params str date: user inputed date
    :param str intervals: time intervals, e.g. '60m 1d 1wk'

    :returns: the day that should be considered as the last
    :rtype: str
    """

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
    """
    Makes sure folder exists in the filesystem to draw and save the plot

    :param str timeframe: name of the timeframe to create a folder

    :returns: a path that was created
    :rtype: str
    """
    today = date.today().strftime("%Y_%m_%d")
    if not os.path.exists(
            os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    f"../analysis/{today}/{timeframe}"))):
        os.makedirs(
            os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    f"../analysis/{today}/{timeframe}")))

    return os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    f"../analysis/{today}/{timeframe}"))

def bid_ask_spread(ticker):
    """
    Calculates the spread between the ask and the bid for the option of a stock.
    If the ask/bid >= 2, the stock is not considered because it has high
    volatility

    :param ticker: name of the stock
    :type ticker: yf.Ticker()

    :returns: whether this stock name should be skipped
    :rtye: bool
    """
    should_skip_ticker = False

    for day in ticker.options:

        # determine days
        d0 = datetime.strptime(date.today().strftime("%Y-%m-%d"), '%Y-%m-%d')
        d1 = datetime.strptime(day, '%Y-%m-%d')
        delta = d1 - d0

        # make sure enough days passed
        if delta.days > 40:
            # retrieve option chain
            opt = ticker.option_chain(day)
            # only looking at calls NOT puts, but vollatility should be similar
            calls = opt.calls
            # get those call out of the money (they do not have intrinsic value)
            OTM = calls[ calls['inTheMoney']==False ][ ['bid','ask'] ].reset_index(drop=True)
            try:
                ask = OTM.loc[0][1] # get ask
                bid = OTM.loc[0][0] # get bid
                if (ask/bid) >= 2:
                    print(f"""
                        {ticker.info['symbol']} ATM ask({ask}) is > 2 times
                        the bid({bid}), is a different timezone, and data is closed?
                    """)
                    should_skip_ticker = True
            except (RuntimeWarning, KeyError):
                print(f"{ticker.info['symbol']} ATM bid or ask is missing")
                continue
            break

    return should_skip_ticker

def relative_strength(prices, n=14):
    """
    Compute the n period relative strength indicator
    http://stockcharts.com/school/doku.php?id=chart_school:glossary_r#relativestrengthindex
    http://www.investopedia.com/terms/r/rsi.asp

    :param series prices: dataset of the stock
    :param int n: represents the period to lookback in terms of candles

    :returns: the value of RSI
    :rtype: float
    """

    deltas = np.diff(prices)
    seed = deltas[:n + 1]
    up = seed[ seed >= 0] .sum() / n
    down = -seed[ seed < 0 ].sum() / n
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:n] = 100. - 100. / (1. + rs)

    for i in range(n, len(prices)):
        delta = deltas[i - 1]  # cause the diff is 1 shorter

        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (n - 1) + upval) / n
        down = (down * (n - 1) + downval) / n

        rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi
