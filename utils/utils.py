from pandas import DataFrame
from typing import List
import yfinance as yf
import pandas as pd
import sqlite3
import sqlite3
import itertools


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


def compute_momentum(df: DataFrame) -> DataFrame:
    return ((df["Close"][-1] - df["Close"][0]) / df["Close"][0]) if not df.empty else 0


def get_data_from_yahoo(
    ticker: str, start_date: str, end_date: str, max_attempts: int = 5
):
    for i in range(max_attempts):
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if not df.empty:
            return df
        else:
            pass
    return pd.DataFrame()  # return an empty DataFrame if all attempts fail


def get_data_from_db(ticker: str, start_date: str, end_date: str):
    conn = sqlite3.connect("data/sp500_hist_data.db")
    query = f"""
                SELECT 
                    date as Date, 
                    open as Open,
                    high as High,
                    low as Low,
                    Close, 
                    adjusted_close as "Adj Close",
                    volume as Volume
                FROM
                    hist_data 
                WHERE 
                    ticker = '{ticker}' 
                    AND date >= '{start_date}' 
                    AND date <= '{end_date}'
            """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.date
    df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True, drop=True)
    df.drop("Date", axis=1, inplace=True)
    return df


def get_data(ticker: str, start_date: str, end_date: str, source: str = "yahoo"):
    if source == "db":
        return get_data_from_db(ticker, start_date, end_date)
    elif source == "yahoo":
        return get_data_from_yahoo(ticker, start_date, end_date)


def set_index_to_column(db_path: str, table_name: str, column_name: str) -> None:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    sql = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{column_name} ON {table_name} ({column_name});"
    c.execute(sql)
    conn.commit()
    conn.close()


def create_parameter_combinations(param_dict: dict[str, list]) -> dict[str]:
    keys, values = zip(*param_dict.items())
    combinations_dicts = [dict(zip(keys, v)) for v in itertools.product(*values)]
    return combinations_dicts


def load_sp500_historic_tickers() -> pd.DataFrame:
    conn = sqlite3.connect("data/sp500_hist_data.db")
    query = "SELECT ticker, date_added, date_removed, enough_data, more_than_2_yrs, ext_days, earliest_date FROM tickers"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Ugly hack to convert the string values to the correct types
    df["date_added"] = pd.to_datetime(df["date_added"])
    df["date_removed"] = pd.to_datetime(df["date_removed"])
    df["earliest_date"] = pd.to_datetime(df["earliest_date"])
    df["ext_days"] = df["ext_days"].astype("float")
    df["enough_data"] = df["enough_data"] == "True"
    df["more_than_2_yrs"] = df["more_than_2_yrs"] == "True"
    return df


def get_current_universe(df: pd.DataFrame, date) -> List[str]:
    # Convert the date to a pandas datetime object for comparison
    specified_date = pd.to_datetime(date)

    return df[
        (df["date_added"] <= specified_date)
        & ((df["date_removed"].isnull()) | (df["date_removed"] >= specified_date))
    ]["ticker"].tolist()
