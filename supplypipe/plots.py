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
