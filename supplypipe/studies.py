# -*- coding: utf-8 -*-

from supplypipe.downloader import download
from supplypipe.plots import mtf
from supplypipe.utils import check_if_folder_exists, setup_ohlc, \
                             determine_today_yesterday

def oneDay_oneWeek(security, intervals, on_demand=""):
    """
    Use 1D and 1W in terms of the EMA crossovers. Consider 1W as the bigger
    frame 'tide'. Consider the 1D, as the 'wave'. Meanwhile the 1W is crossed
    UP, you can only buy at 1D

    :param str security: name of the stock/s
    :param intervals: time intervals, e.g. '60m 1d 1wk' (normally comes from the
    use command line arguments)
    :param str on_demand: will not take into consideration the securities of the
    config and will not take into account the EMA conditions for crossover
    """

    today, yesterday = determine_today_yesterday()

    print(f"Downloading security: {security}")
    hour, day, week = download(security, intervals)
    # resample the hour dataset to 4 hours
    hour4 = hour.resample('4H').agg(setup_ohlc()).dropna()
    # resample to business day
    oneD = hour.resample('B').mean()
    # create EMAs
    exp3 = day['Close'].ewm(span=3, adjust=True).mean()
    exp5 = week['Close'].ewm(span=5, adjust=True).mean()
    exp7 = hour4['Close'].ewm(span=7, adjust=True).mean() 
    exp15 = day['Close'].ewm(span=15, adjust=True).mean()
    exp15_w = week['Close'].ewm(span=15, adjust=True).mean()
    exp21 = hour4['Close'].ewm(span=21, adjust=True).mean()

    if on_demand:
        # do only plot with whatever results are for the given dates
        print(f"\nGenerating plot on demand for {security}. The current " + \
              "strategies are plotted, but are not checked if their " + \
              "rules/conditions apply.")
        mtf(security, check_if_folder_exists("on_demand"), hour4, day, week,
            exp3,exp5,exp7,exp15,exp15_w,exp21)

        return

    try:
        # check whether 1D > 1W using 'today' and 'yesterday' EMA values
        # this will mean a positive result equivalent to buying
        buy_oneD_oneW = exp3.loc[today] > exp15.loc[today] and \
                        exp3.loc[yesterday] < exp15.loc[yesterday] and \
                        exp5.loc[today] > exp15_w.loc[today]
        # check whether 1D < 1W using 'today' and 'yesterday' EMA values
        # this will mean a negative result equivalent to selling
        sell_oneD_oneW = exp3.loc[today] < exp15.loc[today] and \
                         exp3.loc[yesterday] > exp15.loc[yesterday] and \
                         exp5.loc[today] < exp15_w.loc[today]

        if buy_oneD_oneW:
            # BUY signal
            mtf(security, check_if_folder_exists("1D/BUY"), hour4, day, week,
                exp3, exp5, exp7, exp15, exp15_w, exp21)
            print(f"Checks conditions in the BUY direction of current strategy")
        elif sell_oneD_oneW:
            # SELL signal
            mtf(security, check_if_folder_exists("1D/SELL"), hour4, day, week,
                exp3, exp5, exp7, exp15, exp15_w, exp21)
            print(f"Checks conditions in the SELL direction of current strategy")
        else:
            print("Conditions of current strategy cannot be satisfied " +\
                  f"for {security} ... exiting")
    except (KeyError, IndexError) as e:
        print(f"{security} does not yet have TODAY's data, try again later")

def fourHour_oneDay():
    """Use 4H and 1D. Consider 1D as the bigger frame 'tide'.
    Consider the 4H, as the 'wave'. Meanwhile the 1D is crossed
    UP, you can only buy at 4H
    """
    pass

def fourHour_oneDay_oneWeek():
    """Use 4H, 1D and 1W. Consider 1W as the bigger frame 'tide'.
    Consider the 4H, 1D, as the 'wave'. Meanwhile the 1W is crossed
    UP, you can only buy at 4H & 1D
    """
    pass