from pandas import DataFrame
from typing import List
import yfinance as yf
import pandas as pd
import sqlite3


def open_positions(df: DataFrame) -> List[str]:
    """Return a list of open positions."""
    latest_buy = (
        df.query("Action=='BUY'")
        .sort_values("Date")
        .groupby("Ticker")["Quantity"]
        .last()
    )
    latest_sell = (
        df.query("Action=='SELL'")
        .sort_values("Date")
        .groupby("Ticker")["Quantity"]
        .last()
    )
    s = latest_buy.subtract(latest_sell, fill_value=0)
    return s[s != 0].index.tolist()


def market_filter(
    self, indicator: str, smaller_than: int, date: str, ignore: bool = True
) -> bool:
    if ignore:
        return ignore
    if indicator != "^VIX":
        raise ValueError("Only ^VIX is supported for the market filter.")
    df = self.get_data(indicator, date, date + timedelta(days=3))
    print("📈 Market filter:", indicator, "|", df["Close"][0])
    return (
        df["Close"][0] < smaller_than
    )  # Wenn Vix> 30, dann verkauf, aber kauf keine neue Position


@staticmethod
def get_data(ticker, start_date, end_date, source: str = "yahoo"):
    if source == "db":
        print("--->> Getting data from db")
        return get_data_from_db(ticker, start_date, end_date)
    elif source == "yahoo":
        return get_data_from_yahoo(ticker, start_date, end_date)


@staticmethod
def compute_momentum(df):
    return ((df["Close"][-1] - df["Close"][0]) / df["Close"][0]) if not df.empty else 0


@staticmethod
def get_data_from_yahoo(
    ticker: str, start_date: str, end_date: str, max_attempts: int = 5
):
    for i in range(max_attempts):
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if not df.empty:
            return df
        else:
            pass
    print("Max attempts exceeded for: ", ticker, start_date, end_date)
    return pd.DataFrame()  # return an empty DataFrame if all attempts fail


@staticmethod
def get_data_from_db(ticker: str, start_date: str, end_date: str):
    conn = sqlite3.connect("histData.db")
    query = f"SELECT date as Date, close FROM hist_data WHERE ticker = '{ticker}' AND date >= '{start_date}' AND date <= '{end_date}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.date
    df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True)
    return df
