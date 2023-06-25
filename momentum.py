import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal
from datetime import datetime, timedelta
import numpy as np
from dateutil.relativedelta import relativedelta
from process_json import get_params
import warnings

warnings.filterwarnings("ignore")  # should be removed in production

data, unique_id = get_params("data")

START_DATE = data["Start_Date"]
END_DATE = data["End_Date"]

STARTING_BALANCE = data["Starting_Balance"]

LOOK_BACK_PERIODS = data["Look_Back_Periods"][0]  # (13, 'm')
SKIP_LAST_PERIOD = data["Skip_Last_Period"]  # False
HOLD_PERIOD = data["Rebalancing"][0]  # (1, 'm')
N_HOLDINGS = data["Holdings"]  # 3
FEE_PER_TRADE = data["Fee_Per_Trade"]


class TradingStrategy:
    def __init__(self, tickers):
        self.tickers = tickers
        self.cash_balance = STARTING_BALANCE
        self.trade_log = pd.DataFrame(
            columns=[
                "Date",
                "Ticker",
                "Action",
                "Quantity",
                "Price",
                "PnL",
                "cash_balance",
                "Timestamp",
                "unique_id",
            ],
        )

    def calculate_momentum(self, ticker, date):
        start_date = date - relativedelta(months=LOOK_BACK_PERIODS)
        one_month = 1 if SKIP_LAST_PERIOD else 0
        momentum_date = date - relativedelta(
            months=one_month
        )  # 2022-05-02 00:00:00 -> 2022-04-02 00:00:00
        df = self.get_data(ticker, start_date, momentum_date)
        return self.compute_momentum(df)

    @staticmethod
    def get_data(ticker, start_date, end_date, max_attempts=5):
        for i in range(max_attempts):
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not df.empty:
                return df
            else:
                pass

        print("Max attempts exceeded for: ", ticker, start_date, end_date)
        return pd.DataFrame()  # return an empty DataFrame if all attempts fail

    @staticmethod
    def compute_momentum(df):
        close_prices = df["Close"]
        return (
            ((close_prices[-1] - close_prices[0]) / close_prices[0])
            if not df.empty
            else 0
        )

    def sell_positions(self, date, trading_fee: float, hold_period: int):
        buy_log = self.trade_log[self.trade_log["Action"] == "BUY"]
        buy_log_grouped = buy_log.groupby("Ticker")["Quantity"].sum()
        sell_log = self.trade_log[self.trade_log["Action"] == "SELL"]
        sell_log_grouped = sell_log.groupby("Ticker")["Quantity"].sum()
        positions = buy_log_grouped.subtract(sell_log_grouped, fill_value=0)

        for ticker in positions.index:
            if positions[ticker] > 0:
                last_buy_date = buy_log[buy_log["Ticker"] == ticker]["Date"].max()
                if (date - last_buy_date).days >= (30 * hold_period):
                    self.sell_position(ticker, date, trading_fee)

    def sell_position(self, ticker, date, trading_fee):
        df = self.get_data(ticker, date, date + timedelta(days=3))
        if not df.empty:
            self.execute_sell(df, ticker, date, trading_fee)

    def execute_sell(self, df, ticker, date, trading_fee):
        quantity_to_sell = (
            self.trade_log[
                (self.trade_log["Ticker"] == ticker)
                & (self.trade_log["Action"] == "BUY")
            ]["Quantity"].sum()
            - self.trade_log[
                (self.trade_log["Ticker"] == ticker)
                & (self.trade_log["Action"] == "SELL")
            ]["Quantity"].sum()
        )

        if quantity_to_sell > 0:
            current_price = df["Close"][-1]
            sell_price = quantity_to_sell * current_price
            sell_price -= trading_fee
            self.cash_balance += quantity_to_sell * current_price
            buy_price = self.trade_log[
                (self.trade_log["Ticker"] == ticker)
                & (self.trade_log["Action"] == "BUY")
            ]["Price"].values[0]
            trade_pnl = (current_price - buy_price) * quantity_to_sell
            print(
                "🛒 Sell",
                ticker,
                "for 💵 ",
                np.round(quantity_to_sell * current_price, 2),
                "USD",
                "| 💰 PnL: ",
                np.round(trade_pnl, 2),
            )

            self.trade_log = self.trade_log.append(
                {
                    "Date": date,
                    "Ticker": ticker,
                    "Action": "SELL",
                    "Quantity": np.round(quantity_to_sell, 2),
                    "Price": np.round(current_price, 2),
                    "PnL": np.round(trade_pnl, 2),
                    "cash_balance": np.round(self.cash_balance, 2),
                    "Timestamp": datetime.now(),
                    "unique_id": unique_id,
                },
                ignore_index=True,
            )

    def buy_positions(self, date, trading_fee, n_holdings):
        tickers_momentum = self.get_tickers_momentum(date)
        cash_per_position = self.cash_balance / n_holdings
        for ticker, momentum in tickers_momentum[:n_holdings]:
            if momentum > 0 and self.cash_balance > 0:
                self.buy_position(ticker, date, cash_per_position)

    def get_tickers_momentum(self, date):
        tickers_momentum = [
            (ticker, self.calculate_momentum(ticker, date)) for ticker in self.tickers
        ]
        tickers_momentum.sort(key=lambda x: x[1], reverse=True)
        print("💼 Ticker |🌀 Momentum")
        _ = [print(i[0], "|", i[1]) for i in tickers_momentum]
        return tickers_momentum

    def buy_position(self, ticker, date, cash_per_position):
        df = self.get_data(ticker, date, date + timedelta(days=3))
        if not df.empty:
            print("🛍️ Buy", ticker, " for 💵 ", np.round(cash_per_position, 2), "USD")
            self.execute_buy(df, ticker, date, cash_per_position, trading_fee=0.5)

    def execute_buy(
        self, df, ticker, date, cash_per_position, trading_fee: float = 0.0
    ):
        current_price = df["Close"][-1]
        cash_per_position -= trading_fee
        quantity = cash_per_position / current_price
        self.cash_balance -= cash_per_position
        self.trade_log = self.trade_log.append(
            {
                "Date": date,
                "Ticker": ticker,
                "Action": "BUY",
                "Quantity": np.round(quantity, 2),
                "Price": np.round(current_price, 2),
                "PnL": None,
                "cash_balance": np.round(self.cash_balance, 2),
                "Timestamp": datetime.now(),
                "unique_id": unique_id,
            },
            ignore_index=True,
        )

    def run(self, start_date, end_date):
        print("💫 New run:", datetime.now())
        print("💼 Tickers: ", self.tickers)
        print("Top N holdings: ", N_HOLDINGS)
        nyse = mcal.get_calendar("NYSE")
        trading_days = nyse.schedule(start_date=start_date, end_date=end_date).index
        for date in pd.date_range(start_date, end_date, freq="MS"):
            closest_trading_day = self.get_closest_trading_day(date, trading_days)
            print("🌱 New month:", date, "------")
            print(" New day:", closest_trading_day, "------")
            if not self.trade_log.empty:
                self.sell_positions(closest_trading_day, FEE_PER_TRADE, HOLD_PERIOD)
            self.buy_positions(closest_trading_day, FEE_PER_TRADE, N_HOLDINGS)
        self.save_log()

    @staticmethod
    def get_closest_trading_day(date, trading_days):
        closest_trading_day_index = trading_days.searchsorted(date)
        return trading_days[closest_trading_day_index]

    def save_log(self):
        if not self.trade_log.empty:
            with open("data/trade_log.csv", "a") as f:
                self.trade_log.to_csv(f, header=f.tell() == 0, index=False)


universe = [
    "XLK",
    "XLV",
    "XLF",
    "XLY",
    "XLC",
    "XLI",
    "XLP",
    "XLU",
    "XLE",
    "XLRE",
    "XLB",
]

exclusion_list = [
    "XLU",
    "XLE",
    "XLRE",
    "XLB",
]

trade_list = [ticker for ticker in universe if ticker not in exclusion_list]
strategy = TradingStrategy(trade_list)

strategy.run(START_DATE, END_DATE)
