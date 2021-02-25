import yfinance as yf

def download(list_of_securities, **kwargs):

	data = yf.download(list_of_securities,
					   group_by='ticker',
					   auto_adjust=True,
		               **kwargs)

	return data
