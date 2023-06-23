import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime
import pandas_market_calendars as mcal


class TradingSimulator:
    @staticmethod
    def get_data(ticker, start_date, end_date, max_attempts=5):
        for i in range(max_attempts):
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not df.empty:
                return df
            else:
                pass

    @staticmethod
    def get_closest_trading_day(date, trading_days):
        closest_trading_day_index = trading_days.searchsorted(date)
        return trading_days[closest_trading_day_index]

    @staticmethod
    def trade(ticker, buy_date, sell_date, capital, filename="trade_log.tsv"):
        data = TradingSimulator.get_data(ticker, buy_date, sell_date)
        if data is not None and not data.empty:
            nyse = mcal.get_calendar("NYSE")
            trading_days = nyse.schedule(start_date=buy_date, end_date=sell_date).index
            buy_date = TradingSimulator.get_closest_trading_day(
                np.datetime64(buy_date), trading_days
            )
            sell_date = TradingSimulator.get_closest_trading_day(
                np.datetime64(sell_date), trading_days
            )

            buy_price = data.loc[buy_date, "Open"]
            sell_price = data.loc[sell_date, "Close"]

            quantity = capital / buy_price
            pnl = (sell_price - buy_price) * quantity

            with open(filename, "a") as f:
                f.write(
                    f"{datetime.now()}\t{ticker}\t'buy'\t{buy_price}\t{buy_date}\t'N/A'\n"
                )
                f.write(
                    f"{datetime.now()}\t{ticker}\t'sell'\t{sell_price}\t{sell_date}\t{pnl}\n"
                )


# Buy and sell simulation
buy_date = "2022-02-01"
sell_date = "2023-03-01"
# TradingSimulator.trade("SPY", buy_date, sell_date, 100_000)

data = TradingSimulator.get_data("SPY", buy_date, sell_date)
print(data.index)
