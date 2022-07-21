# -*- coding: utf-8 -*-

import yfinance as yf
from supplypipe.utils import calculate_download_days

def download(list_of_securities, intervals, **kwargs):

	intervals = intervals.replace(',',' ').split()
	start_date4H, end_date4H = calculate_download_days(29)
	start_date1D, end_date1D = calculate_download_days(370)
	start_date1W, end_date1W = calculate_download_days(700)

	h = yf.download(list_of_securities,
					   group_by='ticker',
					   auto_adjust=True,
					   interval=intervals[0],
					   period='max',
		               #**kwargs)
		               start=start_date4H,
		               end=end_date4H,threads = False)
		               #prepost = True)

	D = yf.download(list_of_securities,
					   group_by='ticker',
					   auto_adjust=True,
					   interval=intervals[1],
					   period='max',
		               start=start_date1D,
		               end=end_date1D,
		               prepost = True,threads = False)

	W = yf.download(list_of_securities,
					   group_by='ticker',
					   auto_adjust=True,
					   interval=intervals[2],
					   period='max',
		               start=start_date1W,
		               end=end_date1W,
		               prepost = True,threads = False)

	return h, D, W
