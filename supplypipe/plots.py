import mplfinance as mpf
import matplotlib.pyplot as plt

def mtf(security,path,hour4, day, week, exp3, exp5, exp7, exp15, exp15_w, exp21):
    """Plot multitimeframe"""
    mc = mpf.make_marketcolors(up='g',down='r',volume='in')
    s  = mpf.make_mpf_style(marketcolors=mc)
    # #s = mpf.make_mpf_style(base_mpf_style='binance',rc={'figure.facecolor':'lightgray'})
    # apds = [mpf.make_addplot(exp3,color='red'),
    #          mpf.make_addplot(exp15,color='green')]
    # # #mpf.plot(hour4,type='renko',renko_params=dict(brick_size='atr', atr_length=2))
    # fig, axes = mpf.plot(day,type='candle',addplot=apds,figscale=1.5,figratio=(7,5),title='\n\nTEST',
    #                   style=s,returnfig=True,volume=True)
    # mpf.show()
    # breakpoint()

    # 3 in one figures
    fig = mpf.figure(figsize=(20,35),style=s)
    ax1 = fig.add_subplot(4,1,1)
    ax2 = fig.add_subplot(4,1,2)
    ax3 = fig.add_subplot(4,1,3)
    ax4 = fig.add_subplot(4,1,4)
    seven_twenty_one = [mpf.make_addplot(exp7,color='red',ax=ax1),mpf.make_addplot(exp21,color='green',ax=ax1)]
    three_fifteen = [mpf.make_addplot(exp3,color='red',ax=ax2),mpf.make_addplot(exp15,color='green',ax=ax2)]
    five_fifteen = [mpf.make_addplot(exp5,color='red',ax=ax3),mpf.make_addplot(exp15_w,color='green',ax=ax3)]
    mpf.plot(hour4,type='candle',ax=ax1,axtitle='4H',addplot=seven_twenty_one,xrotation=0)
    mpf.plot(day,type='candle',ax=ax2,axtitle='1D',volume=ax4,addplot=three_fifteen,xrotation=0)
    mpf.plot(week ,type='candle',ax=ax3,axtitle='1W',addplot=five_fifteen,xrotation=0)
    plt.suptitle(f"{security.upper()}")
    plt.savefig(f'{path}/{security.upper()}.pdf',dpi=96)

def elder_impulse_system(security,path,hour4,week,exp13_w):
    """Based on MACD and a EMA directions

    weekly
    green = (EMA_current > EMA_previous) and (MACD_current > MACD_previous) 
    red = (EMA_current < EMA_previous) and (MACD_current < MACD_previous) 

    4H
    for every_4_h in hour4:
        calculate_weekly_elder_signal()
        update_plot()

    Original source code from TradingView
    //
    // @author LazyBear
    //
    // If you use this code in its original/modified form, do drop me a note. 
    //
    study("Elder Impulse System [LazyBear]", shorttitle="EIS_LB")
    useCustomResolution=input(false, type=bool)
    customResolution=input("D", type=resolution)
    source = security(tickerid, useCustomResolution ? customResolution : period, close)
    showColorBars=input(false, type=bool)
    lengthEMA = input(13)
    fastLength = input(12, minval=1), slowLength=input(26,minval=1)
    signalLength=input(9,minval=1)

    calc_hist(source, fastLength, slowLength) =>
        fastMA = ema(source, fastLength)
        slowMA = ema(source, slowLength)
        macd = fastMA - slowMA
        signal = sma(macd, signalLength)
        macd - signal

    get_color(emaSeries, macdHist) =>
        g_f = (emaSeries > emaSeries[1]) and (macdHist > macdHist[1])
        r_f = (emaSeries < emaSeries[1]) and (macdHist < macdHist[1])
        g_f ? green : r_f ? red : blue
        
    b_color = get_color(ema(source, lengthEMA), calc_hist(source, fastLength, slowLength))    
    bgcolor(b_color, transp=0)
    barcolor(showColorBars ? b_color : na)

    """
    pass
