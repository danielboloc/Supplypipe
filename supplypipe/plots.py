# -*- coding: utf-8 -*-

import mplfinance as mpf
import matplotlib.pyplot as plt

def mtf(security,path,hour4, day, week, exp3, exp5, exp7, exp15, exp15_w, exp21):
    """
    Plot multi-timeframe data. Currently is not very optimized, but rather it
    focuses on 4H, 1D and 1W exponential moving averages.
    
    :param str security: name of the stock
    :param str path: path in the current filesystem to draw the plots
    :param dataframe hour4: data resamples at 4 hours
    :param dataframe day: data resamples at 1 day
    :param dataframe week: data resamples at 1 week
    :param series exp3: EMA of length 3 for hour
    :param series exp5: EMA of length 5 for hour
    :param series exp7: EMA of length 7 for hour
    :param series exp15: EMA of length 15 for hour
    :param series exp15_w: EMA of length 15 for week
    :param series exp21: EMA of length 21 for week
    """

    # initialize settings, where if price is up the color is green, down is red,
    # and to include the volume
    print("\nSetting up plots\n")
    mc = mpf.make_marketcolors(up='g',down='r',volume='in')
    s  = mpf.make_mpf_style(marketcolors=mc)

    # create four axes in the figure
    fig = mpf.figure(figsize=(20,35),style=s)
    ax1 = fig.add_subplot(4,1,1)
    ax2 = fig.add_subplot(4,1,2)
    ax3 = fig.add_subplot(4,1,3)
    ax4 = fig.add_subplot(4,1,4)
 
    print("Drawing EMAs")
    # create the EMA crossover lines
    seven_twenty_one = [ mpf.make_addplot(exp7,color='red',ax=ax1),
                         mpf.make_addplot(exp21,color='green',ax=ax1) ]
    three_fifteen = [ mpf.make_addplot(exp3,color='red',ax=ax2),
                      mpf.make_addplot(exp15,color='green',ax=ax2) ]
    five_fifteen = [ mpf.make_addplot(exp5,color='red',ax=ax3),
                     mpf.make_addplot(exp15_w,color='green',ax=ax3) ]
 
    print("Plotting candlesticks")
    # plot the data in candlesticks at various timeframes, and add EMA lines
    mpf.plot(hour4, type='candle', ax=ax1, axtitle='4H',
             addplot=seven_twenty_one, xrotation=0)
    mpf.plot(day, type='candle', ax=ax2, axtitle='1D', volume=ax4, 
             addplot=three_fifteen, xrotation=0)
    mpf.plot(week, type='candle', ax=ax3,axtitle='1W', addplot=five_fifteen,
             xrotation=0)
    print("Saving plot")
    plt.suptitle(f"{security.upper()}")
    plt.savefig(f'{path}/{security.upper()}.pdf',dpi=96)
    print("DONE\n")