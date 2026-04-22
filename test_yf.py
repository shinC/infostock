import yfinance as yf
def test_fetch(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if "regularMarketChangePercent" in info:
            change = info["regularMarketChangePercent"]
            # To get the date without large history overhead
            data = t.history(period="1d")
            last_date = data.index[-1].strftime("%Y-%m-%d") if not data.empty else None
            return round(change, 2), last_date
    except Exception as e:
        print("error", e)
print(test_fetch("CL=F"))
