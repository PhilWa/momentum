from pandas import DataFrame
from typing import List


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


# high and low optimizated trend checker
# Sequece momentum
