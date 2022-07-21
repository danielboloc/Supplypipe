# -*- coding: utf-8 -*-

import yfinance as yf
from supplypipe.utils import calculate_download_days

def download(list_of_securities, intervals, **kwargs):
	"""
	Downloads data at different intervals (timeframes) for a list of securities
	or stocks

	:param list list_of_securities: stocks written in capital letters, i.e. AMD
	:param str intervals: time intervals, e.g. '60m 1d 1wk'
	:param dict kwargs: multiple option settings to be specified
	"""

	# make sure interval string has no commas
	intervals = intervals.replace(',',' ').split()
	# for each interval determine the max days data is available
	start_date4H, end_date4H = calculate_download_days(29)
	start_date1D, end_date1D = calculate_download_days(370)
	start_date1W, end_date1W = calculate_download_days(700)

	# download the data (could be optimized further to avoid code duplication)
	h = yf.download(list_of_securities, group_by='ticker', auto_adjust=True,
					interval=intervals[0], period='max', start=start_date4H,
		            end=end_date4H,threads = False)

	D = yf.download(list_of_securities, group_by='ticker', auto_adjust=True,
					interval=intervals[1], period='max', start=start_date1D,
		            end=end_date1D, prepost = True,threads = False)

	W = yf.download(list_of_securities, group_by='ticker', auto_adjust=True, 
	                interval=intervals[2], period='max', start=start_date1W,
		            end=end_date1W, prepost = True,threads = False)

	return h, D, W
