from supplypipe.downloader import download
from supplypipe.utils import relative_strength
import mplfinance as mpf
import matplotlib.pyplot as plt
from numpy import arange
from scipy.stats import linregress        
from datetime import timedelta, date, datetime
import os
import time
import yfinance as yf
import pandas as pd

ohlc_dict = {                                                                                                             
    'Open':'first',                                                                                                    
    'High':'max',                                                                                                       
    'Low':'min',                                                                                                        
    'Close': 'last',                                                                                                    
    'Volume': 'sum'                                                                                                        
}

def download_security_data(security):
    day = yf.download(security,period="max",group_by='ticker',auto_adjust=True)
    week = yf.download(security,period="max",group_by='ticker',auto_adjust=True,interval="1wk")

    return { 'day': day, 'week': week }

def moving_average_cross(data, length_small, length_large, period='day'):

    if period == 'day':
        timeframe = data['day']
    elif period == 'week':
        timeframe = data['week']

    smallEMA = timeframe['Close'].ewm(span=length_small, adjust=True).mean()
    largeEMA = timeframe['Close'].ewm(span=length_large, adjust=True).mean()

    return smallEMA, largeEMA

def run(security):
    print(f"Working on {security} . . .")
    data = download_security_data(security)
    day150, day200 = moving_average_cross(data,150,200,'day')
    day50, day150 = moving_average_cross(data,50,150,'day')
    week30, week40 = moving_average_cross(data,30,40,'week')
    day50_2_years = day50.loc["2020":"2021",].copy()
    day150_2_years = day150.loc["2020":"2021",].copy()
    day200_2_years = day200.loc["2020":"2021",].copy()
    week30_2_years = week30.loc["2020":"2021",].copy()
    week40_2_years = week40.loc["2020":"2021",].copy()
    #fourHsmall, fourHlarge = moving_average_cross(data,7,21,'4h')
    mc = mpf.make_marketcolors(up='g',down='r',volume='in')
    s  = mpf.make_mpf_style(marketcolors=mc)
    fig = mpf.figure(figsize=(20,35),style=s)
    ax1 = fig.add_subplot(4,1,1)
    ax2 = fig.add_subplot(4,1,2)
    ax3 = fig.add_subplot(4,1,3)
    ax4 = fig.add_subplot(4,1,4)
    day_50_150 = [mpf.make_addplot(day50_2_years,color='red',ax=ax1),
                  mpf.make_addplot(day150_2_years,color='green',ax=ax1)]
    day_150_200 = [mpf.make_addplot(day150_2_years,color='red',ax=ax2),
                  mpf.make_addplot(day200_2_years,color='green',ax=ax2)]
    week_30_40 = [mpf.make_addplot(week30_2_years,color='red',ax=ax3),
                  mpf.make_addplot(week40_2_years,color='green',ax=ax3)]

    data_2_years = data["day"].loc["2020":"2021",]
    data_week_2_years = data["week"].loc["2020":"2021",]
    last_price = data['day']['Close'].values.tolist()[-1] # last price
    last_50_sma = day50.values.tolist()[-1]
    last_150_sma = day150.values.tolist()[-1]
    last_200_sma = day200.values.tolist()[-1]
    slope_200_days = linregress(arange(60),day200.values.tolist()[-60:]).slope
    min_week52 = min(data['day']['Low'].values.tolist()[-250:])
    max_week52 = max(data['day']['High'].values.tolist()[-250:])
    percent_30_above_min_week52 = min_week52 * 1.3
    percent_25_within_max_week52 = max_week52 * 0.75
    rsi = relative_strength(data['day']['Close'])

    # Fundamental analysis
    ticker = yf.Ticker(security)
    try:
        qe = ticker.quarterly_earnings
        ae = ticker.earnings
        # Net Profit margin = Net Profit ⁄ Total revenue x 100
        qe["net_profit_margin"] = (qe["Earnings"]/qe["Revenue"])*100
        slope_quart_earn = linregress(arange(len(qe.index)),qe.net_profit_margin.values.tolist()).slope

        ae["net_profit_margin"] = (ae["Earnings"]/ae["Revenue"])*100
        slope_annual_earn = linregress(arange(len(ae.index)),ae.net_profit_margin.values.tolist()).slope
    except KeyError:
        print(f"security gave error to earnings, skipping . . .")
        return

    if last_price > last_150_sma and last_price > last_200_sma:
        if last_150_sma > last_200_sma:
            if slope_200_days > 0:
                if last_50_sma > last_150_sma and last_50_sma > last_200_sma:
                    if last_price > last_50_sma:
                        if last_price >= percent_30_above_min_week52:
                            if last_price >= percent_25_within_max_week52:
                                if slope_annual_earn >= 0.5:
                                    today = date.today()
                                    year = today.year
                                    month = today.strftime("%B").upper()
                                    day = today.strftime("%d")
                                    if not os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), f"analysis/Mark_Minervini/{year}/{month}/{day}"))):
                                        os.makedirs(os.path.abspath(os.path.join(os.path.dirname(__file__), f"analysis/Mark_Minervini/{year}/{month}/{day}")))

                                    path = os.path.abspath(os.path.join(os.path.dirname(__file__), f"analysis/Mark_Minervini/{year}/{month}/{day}"))

                                    print(f"{security} fits all 8 filters")
                                    mpf.plot(data_2_years,type='candle',ax=ax1,axtitle='1D_50_150_SMA',volume=ax4,addplot=day_50_150,xrotation=0)
                                    mpf.plot(data_2_years,type='candle',ax=ax2,axtitle='1D_150_200_SMA',addplot=day_150_200,xrotation=0)
                                    mpf.plot(data_week_2_years,type='candle',ax=ax3,axtitle='1W_30_40_SMA',addplot=week_30_40,xrotation=0)
                                    plt.suptitle(f"{security.upper()}")
                                    plt.savefig(f'{path}/{security.upper()}.pdf',dpi=96)
                                    plt.close()

if __name__ == '__main__':
    # Do this a bit manuall and explicit, but I want to see all the sectors and stocks I'm watching
    # Looking at top 3 + middle 3 in each sector. They will be defined in separate list and joined
    # First list are the leading, then the second list are the middle
    # Define sectors
    # COG remove, it was delisted
    energy = ["MRO","NWS","NOV","KMI","APA","HAL","BKR","WMB","OXY","SLB","DVN"]
    materials = ["AMCR","MOS","FCX","CTVA","CF","WRK"]
    industrials = ["AAL","NLSN","HWM","CSX","ROL","DAL","UAL","LUV","IR"]
    utilities = ["AES","NI","CNP","PPL","FE","NRG","EXC"]
    healthcare = ["VTRS","OGN","BSX","PRGO","PFE","CAH"]
    financials = ["HBAN","PBCT","RF","KEY","IVZ","UNM","BEN","FITB","BAC","CFG","WFC","SYF","BK"]
    discretionary = ["F","HBI","UA","UAA","CCL","GPS","NCLH","NWL","TPR","BWA","MGM","LVS","LEG","GM","PHM"]
    staples = ["CAG","KHC","HRL","CPB","TAP","KR","MO"]
    it = ["HPE","WU","NLOK","HPQ","JNPR","DXC","GLW","INTC","WDC","CSCO"]
    communication = ["LUMN","NWS","NWSA","DISCK","DISCA","T","FOX","FOXA","IPG","VIAC","DISH","VZ"]
    realestate = ["HST","KIM","WY","PEAK","VNO","IRM","DRE"]
    growth = ["FCX","ROST","COP","SQ","NTES","NLS","FVRR","EDIT","IRBT","TWTR","CRSP"]

    sectors = energy + materials + industrials + utilities + healthcare + financials +\
              discretionary + staples + it + communication + realestate + growth
    for stock in sectors:
        time.sleep(0.1)
        run(stock)
