from config import get_configuration
import yfinance as yf
import click
import plotly.graph_objects as go

@click.command()
@click.option("--only-stock",
	          help="To only look at the 'stock' section in config")
@click.option("--on-demand",
	          help="You can put the ticker symbol, e.g MSFT or multiple MSFT, AAPL")
def main(only_stock, on_demand):
	config = get_configuration()
	# tickers = yf.Tickers(config["SECTORS"]["technology"])
	# print(tickers.tickers.QQQ.history(period="1mo"))
	# print(tickers.tickers.QQQ.major_holders)
	for sector in config["SECTORS"]:
		print(f"Downloading sector: {sector}")
		data = yf.download(config["SECTORS"][sector],
						   group_by='ticker',
						   auto_adjust=True,
			               start='2021-01-01',
			               end='2021-02-18')

		for security in config["SECTORS"][sector].split(", "):
			df = data[security]
			fig = go.Figure(data=[go.Candlestick(x=df.loc['2021-01-01':'2021-02-18'],
			                open=df['Open'],
			                high=df['High'],
			                low=df['Low'],
			                close=df['Close'])])

			fig.show()
			breakpoint()

if __name__ == '__main__':
	main()