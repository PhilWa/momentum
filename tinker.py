# monthly_heatmap

import quantstats as qs

# extend pandas functionality with metrics, etc.
qs.extend_pandas()

tickers = {
    "META": 0.2,
    "AAPL": 0.2,
    "AMZN": 0.2,
    "NFLX": 0.2,
    "GOOG": 0.2,
}
stocks = qs.utils.make_index(tickers)
qs.reports.html(stocks, "QQQ", output="dummy.html")
