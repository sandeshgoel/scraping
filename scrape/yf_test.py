import yfinance as yf
import sys

sym = sys.argv[1] if len(sys.argv)>1 else 'AAPL'
res = yf.Ticker(sym)
print(res.info)
print(res.history(period="5d"))
print(res.history(period="1d", interval="30m")['Close'].iloc[-1])