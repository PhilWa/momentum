import pandas as pd
import warnings
import yfinance as yf
import pandas_market_calendars as mcal
from datetime import datetime
from utils.utils import get_data

warnings.filterwarnings("ignore", category=FutureWarning)

### Hello World!
var1 = 1
var2 = 2
var3 = var1 + var2

### IMPORT TRADELOG
# Specify the file path
file_path = r"data/trade_log.csv"

# Read the CSV file into a DataFrame
df_tradeLog = pd.read_csv(file_path)

# Retrieve the latest unique_param_id and unique_run_id
param_id, run_id, experiment_id = df_tradeLog.sort_values(
    by="Timestamp", ascending=False
)[["unique_param_id", "unique_run_id", "unique_experiment_id"]].iloc[0]

# Select latest run from df_tradeLog
df_tradeLog = df_tradeLog[
    (df_tradeLog["unique_param_id"] == param_id)
    & (df_tradeLog["unique_run_id"] == run_id)
]

### GET UNIQUE TICKERS
unique_tickers = df_tradeLog["Ticker"].unique().tolist()


### Create main df with tradingDays as index and columns per ticker
# Create trading calendar for NYSE
nyse = mcal.get_calendar("NYSE")

# Get trading days between start and end dates
start_date = df_tradeLog["Date"].min()
end_date = df_tradeLog["Date"].max()

schedule = nyse.schedule(start_date=start_date, end_date=end_date)
trading_days_list = schedule.index.tolist()
trading_days = schedule.index


### Create df_dailyPortfolio with 'Date' as a normal column
df_dailyPortfolio = pd.DataFrame(trading_days, columns=["Date"])

# Add weekday name from 'Date' and store it in 'weekday' column
df_dailyPortfolio["Date"] = pd.to_datetime(df_dailyPortfolio["Date"])
df_dailyPortfolio["weekday"] = df_dailyPortfolio["Date"].dt.day_name()

### Create dictionary with tradingDays & Qty; qty defaults to 0
ticker_qty_perDay = {day: 0 for day in trading_days_list}

# Create a dictionary for each ticker with trading days and quantity
ticker_qty_dict = {}

# Iterate over each ticker in unique_tickers
for ticker in unique_tickers:
    # Duplicate the ticker_qty_perDay dictionary for the current ticker
    ticker_qty_perDay_copy = ticker_qty_perDay.copy()

    # needed to avoid trying the copy the qty from last entry, if it is the first day
    first_day = True

    # Iterate over every trading day in df_dailyPortfolio
    for date, qty in ticker_qty_perDay.items():
        trading_day = date

        # Copy the quantity from the previous trading day (if it's not the first trading day)
        if first_day == False:
            ticker_qty_perDay_copy[trading_day] = ticker_qty_perDay_copy[
                prev_trading_day
            ]
            # print(f'prev day: {prev_trading_day} had qty: {ticker_qty_perDay_copy[prev_trading_day]}')
        else:
            first_day = False

        # Check if there is a trade in df_tradeLog for the current day
        trades_for_day = df_tradeLog[
            (df_tradeLog["Date"] == trading_day.strftime("%Y-%m-%d"))
            & (df_tradeLog["Ticker"] == ticker)
        ]
        # print(f'{trading_day_short} had the follwing trades: {trades_for_day}')

        if not trades_for_day.empty:
            # Iterate over each trade for the current day
            for trade_index, trade_row in trades_for_day.iterrows():
                trade_type = trade_row["Action"]
                trade_qty = trade_row["Quantity"]
                # Update quantity based on trade type
                if trade_type == "BUY":
                    ticker_qty_perDay_copy[trading_day] += trade_qty
                elif trade_type == "SELL":
                    ticker_qty_perDay_copy[trading_day] -= trade_qty

        prev_trading_day = trading_day

    # Add the ticker_qty_perDay_copy dictionary to df_dailyPortfolio as a new column
    column_name = ticker + "_qty"
    df_dailyPortfolio[column_name] = df_dailyPortfolio["Date"].map(
        ticker_qty_perDay_copy
    )

if False:
    # NEXT: Add historical data for tickers
    def get_data(ticker, start_date, end_date, max_attempts=5):
        for i in range(max_attempts):
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not df.empty:
                return df
            else:
                pass

        print("Max attempts exceeded for:", ticker, start_date, end_date)
        return pd.DataFrame()  # return an empty DataFrame if all attempts fail


for ticker in unique_tickers:
    histData = get_data(ticker, start_date, end_date, source="db")
    df_dailyPortfolio = pd.merge(df_dailyPortfolio, histData, on="Date", how="left")
    df_dailyPortfolio = df_dailyPortfolio.drop(
        ["Open", "High", "Low", "Adj Close", "Volume"], axis=1
    )
    df_dailyPortfolio = df_dailyPortfolio.rename(columns={"Close": f"{ticker}_close"})

for ticker in unique_tickers:
    qty_col = f"{ticker}_qty"
    close_col = f"{ticker}_close"
    product_col = f"{ticker}_sizePosition"
    df_dailyPortfolio[product_col] = (
        df_dailyPortfolio[qty_col] * df_dailyPortfolio[close_col]
    )


df_dailyPortfolio = df_dailyPortfolio.sort_index(axis=1)

# Replace 'sizePosition' with 'positionSize' in column names
df_dailyPortfolio = df_dailyPortfolio.rename(
    columns=lambda x: x.replace("sizePosition", "positionSize")
)


# add daily cash balance
# Iterate over each row in df_dailyPortfolio

df_dailyPortfolio["cash_balance"] = 0
prev_cash_balance = 0

for index, row in df_dailyPortfolio.iterrows():
    date = row["Date"].strftime("%Y-%m-%d")
    # Filter the trade log DataFrame for the given date
    trade_row = df_tradeLog[df_tradeLog["Date"] == date]
    if not trade_row.empty:
        # Get the latest cash balance for the date
        cash_balance = trade_row["cash_balance"].iloc[-1]
        # Update the 'cash_balance' column in df_dailyPortfolio
        df_dailyPortfolio.at[index, "cash_balance"] = cash_balance
    if trade_row.empty:
        # Get the latest cash balance for the date
        if index > 0:
            # prev_cash_balance = df_dailyPortfolio['cash_balance'].shift()
            # Update the 'cash_balance' column in df_dailyPortfolio
            df_dailyPortfolio.at[index, "cash_balance"] = prev_cash_balance

    prev_cash_balance = cash_balance

# order columns
# Get the current column order
columns = df_dailyPortfolio.columns.tolist()

# Remove the "weekday" column from the list
columns.remove("weekday")

# Insert the "weekday" column at the second position
columns.insert(1, "weekday")

# Reorder the columns in the DataFrame
df_dailyPortfolio = df_dailyPortfolio[columns]

# calc totalPositionSize

# Extract the ticker names from the column names
# @CW Question: Why would we recalculate tickers here and not use the unique_tickers list?
tickers = list(
    set(
        [
            col.split("_")[0]
            for col in df_dailyPortfolio.columns
            if col.endswith("_positionSize")
        ]
    )
)

# Calculate the sum of position sizes and store it in a new column
df_dailyPortfolio["total_positionSize"] = df_dailyPortfolio[
    [f"{ticker}_positionSize" for ticker in tickers]
].sum(axis=1)

# calc NetLiq
df_dailyPortfolio["NetLiq"] = (
    df_dailyPortfolio["cash_balance"] + df_dailyPortfolio["total_positionSize"]
)
# Function to convert scientific notation to decimal format
df_dailyPortfolio["NetLiq"] = df_dailyPortfolio["NetLiq"].astype(float)


# calc daily return / change from NetLiq and store as series for qs
df_dailyPortfolio["Return"] = df_dailyPortfolio["NetLiq"].pct_change()

# replace all NaN with 0
df_dailyPortfolio["Return"] = df_dailyPortfolio["Return"].fillna(0)

# delete last row
df_dailyPortfolio = df_dailyPortfolio.drop(df_dailyPortfolio.index[-1])


# Get metrics for the run
import quantstats as qs

qs.extend_pandas()


def get_experiment_metrics(df):
    strategy = pd.Series(df["Return"].values, index=df["Date"])
    return qs.reports.metrics(strategy, mode="full", display=False).T


def calc_cagr(df):
    start_date = df["Date"].min()
    end_date = df["Date"].max()
    years = (end_date - start_date).days / 365
    # Calculate CAGR
    cagr = (df["NetLiq"].iloc[-1] / df["NetLiq"].iloc[0]) ** (1 / years) - 1
    return cagr


def digest_results(df, param_id: str, run_id: str, experiment_id: str):
    custom_cgar = calc_cagr(df)
    res = get_experiment_metrics(df)
    res["custom_cgar"] = custom_cgar
    res["param_id"] = param_id
    res["run_id"] = run_id
    res["experiment_id"] = experiment_id
    res["timestamp"] = datetime.now()
    return res


df_dailyPortfolio = digest_results(df_dailyPortfolio, param_id, run_id, experiment_id)
with open("data/result_log.csv", "a") as f:
    df_dailyPortfolio.to_csv(f, header=f.tell() == 0, index=False)
