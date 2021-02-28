import re
from datetime import timedelta, date

def str2list(string):
	# remove multiple whitespaces to just leave one
	return string.replace(",", " ").split()

def list2str(l):
	return " ".join(" ".join(l).replace(",", " ").split())

def calculate_download_days(days=729):
	"""Since we are dependent of 1h time, we can only retrieve
	up to 730 prior days. Putting 729 to avoid some weird calendar
	missing day.

	The calculation is to get the day of the run - Xdays = 729
	"""
	end_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
	start_date = (date.today() - timedelta(days=days)).strftime('%Y-%m-%d')

	return start_date, end_date

def determine_period(date, intervals):

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