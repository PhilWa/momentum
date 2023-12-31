import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal
from datetime import datetime, timedelta
import numpy as np
from dateutil.relativedelta import relativedelta
import uuid
import warnings
import argparse
from typing import List
from utils import (
    open_positions,
    get_data,
    load_sp500_historic_tickers,
    get_current_universe,
)
from process_json import get_params

warnings.filterwarnings("ignore")  # should be removed in production

### Parametrize script ###

parser = argparse.ArgumentParser(description="Parser for momentum.py parameters")
parser.add_argument(
    "-g", "--grid", default=False, type=bool, help="Activate grid search"
)
args = parser.parse_args()

# Load the parameters from the JSON file
data, PARAMETER_ID = get_params("data")

START_DATE = data["Start_Date"]
END_DATE = data["End_Date"]
STARTING_BALANCE = data["Starting_Balance"]
LOOK_BACK_PERIODS = data["Look_Back_Periods"][0]  # (13, 'm')
SKIP_LAST_PERIOD = data["Skip_Last_Period"]  # False
HOLD_PERIOD = data["Rebalancing"][0]  # (1, 'm')
N_HOLDINGS = data["Holdings"]  # 3
FEE_PER_TRADE = data["Fee_Per_Trade"]

EXPERIMENT_ID = data.get(
    "experiment_id", str(uuid.uuid4())
)  # only present in gridsearch
RUN_ID = str(uuid.uuid4())
DATA_SOURCE = "db"


class TradingStrategy:
    def __init__(self, tickers: List[str] = ["SPY"]):
        self.tickers = tickers
        self.spy_ticker_history = load_sp500_historic_tickers()
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
                "unique_param_id",
                "unique_run_id",
                "unique_experiment_id",
            ],
        )

    def calculate_momentum(self, ticker, date):
        start_date = date - relativedelta(months=LOOK_BACK_PERIODS)
        one_month = 1 if SKIP_LAST_PERIOD else 0
        momentum_date = date - relativedelta(
            months=one_month
        )  # 2022-05-02 00:00:00 -> 2022-04-02 00:00:00
        df = get_data(ticker, start_date, momentum_date, DATA_SOURCE)
        return self.compute_momentum(df)

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
        buy_log_grouped = buy_log.groupby("Ticker")[
            "Quantity"
        ].sum()  # we take all quantity from buy and sell and look at the diff.
        sell_log = self.trade_log[self.trade_log["Action"] == "SELL"]
        sell_log_grouped = sell_log.groupby("Ticker")["Quantity"].sum()
        positions = buy_log_grouped.subtract(sell_log_grouped, fill_value=0)

        for ticker in positions.index:
            if positions[ticker] > 0:
                last_buy_date = buy_log[buy_log["Ticker"] == ticker]["Date"].max()

                # Normalize the dates to the first day of the month
                _date = date.replace(day=1)
                _last_buy_date = last_buy_date.replace(day=1)
                if _date >= _last_buy_date + relativedelta(months=hold_period):
                    self.sell_position(ticker, date, trading_fee)

    def sell_position(self, ticker, date, trading_fee):
        df = get_data(ticker, date, date + timedelta(days=3), DATA_SOURCE)
        if not df.empty:
            self.execute_sell(df, ticker, date, trading_fee)

    def execute_sell(self, df, ticker, date, trading_fee):
        # Get the quantity of the last bought record for this ticker
        quantity_to_sell = (
            self.trade_log[
                (self.trade_log["Ticker"] == ticker)
                & (self.trade_log["Action"] == "BUY")
            ]
            .sort_values(by="Date", ascending=False)["Quantity"]
            .values[0]
        )

        if quantity_to_sell > 0:
            current_price = df["Close"][0]
            self.cash_balance -= trading_fee
            self.cash_balance += quantity_to_sell * current_price
            buy_price = (
                self.trade_log[
                    (self.trade_log["Ticker"] == ticker)
                    & (self.trade_log["Action"] == "BUY")
                ]
                .sort_values(by="Date", ascending=False)["Price"]
                .values[0]
            )
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
                    "unique_param_id": PARAMETER_ID,
                    "unique_run_id": RUN_ID,
                    "unique_experiment_id": EXPERIMENT_ID,
                },
                ignore_index=True,
            )

    def buy_positions(self, date, trading_fee, n_holdings):
        tickers_momentum = self.get_tickers_momentum(date)

        open_tickers = open_positions(self.trade_log)
        can_buy = n_holdings > len(open_tickers)
        cash_per_position = self.cash_balance / n_holdings
        if can_buy:
            for ticker, momentum in tickers_momentum[:n_holdings]:
                if (
                    momentum > 0
                    and (self.cash_balance > 0)
                    and (ticker not in open_tickers)
                ):
                    self.buy_position(ticker, date, cash_per_position, trading_fee)

    def get_tickers_momentum(self, date):
        tickers_momentum = [
            (ticker, self.calculate_momentum(ticker, date)) for ticker in self.tickers
        ]
        tickers_momentum.sort(key=lambda x: x[1], reverse=True)
        print("💼 Ticker |🌀 Momentum")
        # [print(i[0], "|", i[1]) for i in tickers_momentum]
        return tickers_momentum

    def buy_position(self, ticker, date, cash_per_position, trading_fee):
        df = get_data(ticker, date, date + timedelta(days=3), DATA_SOURCE)
        if not df.empty:
            print("🛍️ Buy ", ticker, " for 💵 ", np.round(cash_per_position, 2), "USD")
            self.execute_buy(df, ticker, date, cash_per_position, trading_fee)

    def execute_buy(self, df, ticker, date, cash_per_position, trading_fee):
        share_price = df["Close"][0]
        n_whole_shares = cash_per_position // share_price
        cash_remainder = cash_per_position % share_price
        self.cash_balance -= (cash_per_position - cash_remainder) + trading_fee
        self.trade_log = self.trade_log.append(
            {
                "Date": date,
                "Ticker": ticker,
                "Action": "BUY",
                "Quantity": n_whole_shares,
                "Price": np.round(share_price, 2),
                "PnL": None,
                "cash_balance": np.round(self.cash_balance, 2),
                "Timestamp": datetime.now(),
                "unique_param_id": PARAMETER_ID,
                "unique_run_id": RUN_ID,
                "unique_experiment_id": EXPERIMENT_ID,
            },
            ignore_index=True,
        )

    def run(self, start_date, end_date):
        start_time = datetime.now()
        print(
            "💫 New run:",
            start_time,
            "Starting date: ",
            start_date,
            "End_date:",
            end_date,
        )
        print("💼 Tickers: ", self.tickers)
        print("Top N holdings: ", N_HOLDINGS)
        nyse = mcal.get_calendar("NYSE")
        trading_days = nyse.schedule(start_date=start_date, end_date=end_date).index
        for date in pd.date_range(start_date, end_date, freq="MS"):
            closest_trading_day = self.get_closest_trading_day(date, trading_days)
            print("🌱 New month:", date)
            print(" New day:", closest_trading_day)

            if not self.trade_log.empty:
                self.sell_positions(
                    closest_trading_day,
                    FEE_PER_TRADE,
                    HOLD_PERIOD,
                )

            if DATA_SOURCE == "db":
                self.tickers = get_current_universe(
                    self.spy_ticker_history, closest_trading_day
                )
            self.buy_positions(closest_trading_day, FEE_PER_TRADE, N_HOLDINGS)
        self.sell_positions(closest_trading_day, 0, 0)  # exit all positions

        self.save_log()
        end_time = datetime.now()
        print(
            "🏁 Run complete on:",
            end_time,
            "elapsed time: ",
            end_time - start_time,
            "unique_param_id: ",
            PARAMETER_ID,
        )

    @staticmethod
    def get_closest_trading_day(date, trading_days):
        closest_trading_day_index = trading_days.searchsorted(date)
        return trading_days[closest_trading_day_index]

    def save_log(self):
        if not self.trade_log.empty:
            with open("data/trade_log.csv", "a") as f:
                self.trade_log.to_csv(f, header=f.tell() == 0, index=False)


universe = ["ADI", "ADM", "ADSK", "ADT"]

exclusion_list = [
    "XLRE",
    "XLC",
]

trade_list = [ticker for ticker in universe if ticker not in exclusion_list]
strategy = TradingStrategy()

strategy.run(START_DATE, END_DATE)
