from supplypipe.config import get_configuration
from supplypipe.utils import list2str, calculate_download_days, determine_period
from supplypipe.downloader import download
import yfinance as yf
import click
import plotly.graph_objects as go

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

    print(f"Securities in the current analysis: {securities2download}")
    #hour, day, week = download(securities2download, intervals, **options)
    hour, day, week = download(securities2download, intervals)
    hour4 = hour.resample('4H').mean().dropna()
    oneD = hour.resample('B').mean() # business day
    # plot data with EMAs
        # if is too large split by year
    import pandas as pd
    import mplfinance as mpf
    import matplotlib.pyplot as plt

    exp3 = day['Close'].ewm(span=3, adjust=True).mean()
    exp5 = week['Close'].ewm(span=5, adjust=True).mean()
    exp7 = hour4['Close'].ewm(span=7, adjust=True).mean()
    exp15 = day['Close'].ewm(span=15, adjust=True).mean()
    exp15_w = week['Close'].ewm(span=15, adjust=True).mean()
    exp21 = hour4['Close'].ewm(span=21, adjust=True).mean()
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
    mpf.plot(day,type='candle',ax=ax2,axtitle='1D',addplot=three_fifteen,xrotation=0)
    mpf.plot(week ,type='candle',ax=ax3,axtitle='1W',volume=ax4,addplot=five_fifteen,xrotation=0)
    plt.suptitle("EEM")
    plt.savefig('tsave30.pdf',dpi=90,pad_inches=0.25)

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