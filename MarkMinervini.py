from supplypipe.downloader import download
import mplfinance as mpf
import matplotlib.pyplot as plt
from numpy import arange
from scipy.stats import linregress        

ohlc_dict = {                                                                                                             
    'Open':'first',                                                                                                    
    'High':'max',                                                                                                       
    'Low':'min',                                                                                                        
    'Close': 'last',                                                                                                    
    'Volume': 'sum'                                                                                                        
}

def download_security_data(security):
    hour, day, week = download(security, '60m 1d 1wk')
    hour4 = hour.resample('4H').agg(ohlc_dict).dropna()

    return {'4h': hour4,
            'day': day,
            'week': week}

def moving_average_cross(data, length_small, length_large, period='day'):

    if period == 'day':
        timeframe = data['day']
    elif period == 'week':
        timeframe = data['week']
    elif period == '4h':
        timeframe = data['4h']

    smallEMA = timeframe['Close'].ewm(span=length_small, adjust=True).mean()
    largeEMA = timeframe['Close'].ewm(span=length_large, adjust=True).mean()

    return smallEMA, largeEMA

def run(security):
    data = download_security_data(security)
    day150, day200 = moving_average_cross(data,150,200,'day')
    day50, day150 = moving_average_cross(data,50,150,'day')
    week30, week40 = moving_average_cross(data,30,40,'week')

    #fourHsmall, fourHlarge = moving_average_cross(data,7,21,'4h')
    mc = mpf.make_marketcolors(up='g',down='r',volume='in')
    s  = mpf.make_mpf_style(marketcolors=mc)
    fig = mpf.figure(figsize=(20,35),style=s)
    ax1 = fig.add_subplot(4,1,1)
    ax2 = fig.add_subplot(4,1,2)
    ax3 = fig.add_subplot(4,1,3)
    ax4 = fig.add_subplot(4,1,4)
    day_50_150 = [mpf.make_addplot(day50,color='red',ax=ax1),
                  mpf.make_addplot(day150,color='green',ax=ax1)]
    day_150_200 = [mpf.make_addplot(day150,color='red',ax=ax2),
                  mpf.make_addplot(day200,color='green',ax=ax2)]
    week_30_40 = [mpf.make_addplot(week30,color='red',ax=ax3),
                  mpf.make_addplot(week40,color='green',ax=ax3)]
    last_price = data['day']['Close'].values.tolist()[-1] # last price
    last_50_sma = day50.values.tolist()[-1]
    last_150_sma = day150.values.tolist()[-1]
    last_200_sma = day200.values.tolist()[-1]
    slope_200_days = linregress(arange(60),day200.values.tolist()[-60:]).slope
    min_week52 = min(data['day']['Close'].values.tolist()[-250:])
    max_week52 = max(data['day']['Close'].values.tolist()[-250:])

    #percent_30_above_min_week52 = min_week52 * 1.3
    # if last_price > last_150_sma and last_price > last_200_sma:
    #     if last_150_sma > last_200_sma:
    #         if slope_200_days > 0:
    #             if day50 > day150 and day50 > day200:
    #                 if last_price > day50:
    #                   if last_price >= percent_30_above_min_week52:


    print(week52)
    breakpoint()
    mpf.plot(data['day'],type='candle',ax=ax1,axtitle='1D_50_150_SMA',volume=ax4,addplot=day_50_150,xrotation=0)
    mpf.plot(data['day'],type='candle',ax=ax2,axtitle='1D_150_200_SMA',addplot=day_150_200,xrotation=0)
    mpf.plot(data['week'] ,type='candle',ax=ax3,axtitle='1W_30_40_SMA',addplot=week_30_40,xrotation=0)
    plt.suptitle(f"{security.upper()}")
    plt.savefig(f'/Users/dboloc/Workspace/Supplypipe/analysis/MarkMinervini/{security.upper()}.pdf',dpi=96)

if __name__ == '__main__':
    run('MSFT')
