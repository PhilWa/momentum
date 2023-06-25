import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
from process_json import get_latest_json
import subprocess
import os
import uuid
import json

# Initialize the DataFrame
df = pd.DataFrame(
    columns=[
        "Start_Date",
        "End_Date",
        "Starting_Balance",
        "Look_Back_Periods",
        "Skip_Last_Period",
        "Rebalancing",
        "Holdings",
        "Fee_Per_Trade",
    ]
)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        dbc.Row([dbc.Col(html.H1("Awesome Backtester"), className="mb-4 mt-4")]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label(
                            "Period:", className="mt-4", style={"font-weight": "bold"}
                        ),
                        dcc.DatePickerRange(
                            id="date-range-selector",
                            start_date_placeholder_text="start",
                            end_date_placeholder_text="end",
                            calendar_orientation="horizontal",
                        ),
                    ],
                    md=4,
                ),
                dbc.Col(
                    [
                        html.Label(
                            "Starting Balance:",
                            className="mt-4",
                            style={"font-weight": "bold"},
                        ),
                        dcc.Input(
                            id="starting-balance-input",
                            type="number",
                            placeholder="Enter starting balance",
                            min=0,
                        ),
                    ],
                    md=4,
                ),
                dbc.Col(
                    [
                        html.Label(
                            "Look Back Periods:",
                            className="mt-4",
                            style={"font-weight": "bold"},
                        ),
                        dcc.Dropdown(
                            id="look-back-periods-dropdown",
                            options=[
                                {"label": "3 months", "value": "3m"},
                                {"label": "6 months", "value": "6m"},
                                {"label": "9 months", "value": "9m"},
                                {"label": "12 months", "value": "12m"},
                                {"label": "15 months", "value": "15m"},
                                {"label": "18 months", "value": "18m"},
                                {"label": "21 months", "value": "21m"},
                                {"label": "24 months", "value": "24m"},
                            ],
                            placeholder="Select look back period",
                        ),
                    ],
                    md=4,
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label(
                            "Skip Last Period:",
                            className="mt-4",
                            style={"font-weight": "bold"},
                        ),
                        dcc.Dropdown(
                            id="skip-last-period-dropdown",
                            options=[
                                {"label": "Yes", "value": "yes"},
                                {"label": "No", "value": "no"},
                            ],
                            placeholder="Select skip last period",
                        ),
                    ],
                    md=4,
                ),
                dbc.Col(
                    [
                        html.Label(
                            "Rebalancing:",
                            className="mt-4",
                            style={"font-weight": "bold"},
                        ),
                        dcc.Dropdown(
                            id="rebalancing-dropdown",
                            options=[
                                {"label": "1 month", "value": "1m"},
                                {"label": "2 months", "value": "2m"},
                                {"label": "3 months", "value": "3m"},
                                {"label": "4 months", "value": "4m"},
                                {"label": "5 months", "value": "5m"},
                                {"label": "6 months", "value": "6m"},
                            ],
                            placeholder="Select rebalancing period",
                        ),
                    ],
                    md=4,
                ),
                dbc.Col(
                    [
                        html.Label(
                            "Holdings:", className="mt-4", style={"font-weight": "bold"}
                        ),
                        dcc.Dropdown(
                            id="holdings-dropdown",
                            options=[
                                {"label": "3", "value": 3},
                                {"label": "4", "value": 4},
                                {"label": "5", "value": 5},
                                {"label": "6", "value": 6},
                                {"label": "7", "value": 7},
                                {"label": "8", "value": 8},
                                {"label": "9", "value": 9},
                                {"label": "10", "value": 10},
                            ],
                            placeholder="Select number of holdings",
                        ),
                    ],
                    md=4,
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label(
                            "Fee per Trade:",
                            className="mt-4",
                            style={"font-weight": "bold"},
                        ),
                        dcc.Dropdown(
                            id="fee-per-trade-dropdown",
                            options=[{"label": str(i), "value": i} for i in range(6)],
                            placeholder="Select fee per trade",
                        ),
                    ],
                    md=4,
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button(
                            "Save as JSON",
                            id="save-json-button",
                            n_clicks=0,
                            color="primary",
                            className="mt-4 me-2",
                        ),
                        dbc.Button(
                            "Run Backtest",
                            id="run-backtest-button",
                            n_clicks=0,
                            color="primary",
                            className="mt-4",
                        ),
                    ],
                    md=4,
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col([html.Div(id="output-div", className="mt-4")]),
            ],
        ),
        dbc.Row(
            [
                dbc.Col([html.Div(id="output-div-backtest", className="mt-4")]),
            ],
        ),
    ],
    fluid=True,
)


@app.callback(
    Output("output-div", "children"),
    Input("date-range-selector", "start_date"),
    Input("date-range-selector", "end_date"),
    Input("starting-balance-input", "value"),
    Input("look-back-periods-dropdown", "value"),
    Input("skip-last-period-dropdown", "value"),
    Input("rebalancing-dropdown", "value"),
    Input("holdings-dropdown", "value"),
    Input("fee-per-trade-dropdown", "value"),
    Input("save-json-button", "n_clicks"),
)
def update_output(
    start_date,
    end_date,
    starting_balance,
    look_back_periods,
    skip_last_period,
    rebalancing,
    holdings,
    fee_per_trade,
    save_button_clicks,
):
    if save_button_clicks > 0:
        if start_date is None or end_date is None:
            return "Please select a start date and an end date"
        elif starting_balance is None:
            return "Please enter a starting balance"
        elif look_back_periods is None:
            return "Please select look back periods"
        elif skip_last_period is None:
            return "Please select skip last period"
        elif rebalancing is None:
            return "Please select a rebalancing period"
        elif holdings is None:
            return "Please select number of holdings"
        elif fee_per_trade is None:
            return "Please select fee per trade"
        else:
            # Append selected data to the DataFrame
            global df
            df = df.append(
                {
                    "Start_Date": start_date,
                    "End_Date": end_date,
                    "Starting_Balance": starting_balance,
                    "Look_Back_Periods": look_back_periods,
                    "Skip_Last_Period": skip_last_period,
                    "Rebalancing": rebalancing,
                    "Holdings": holdings,
                    "Fee_Per_Trade": fee_per_trade,
                },
                ignore_index=True,
            )

            # Generate a unique ID for the JSON file
            unique_id = str(uuid.uuid4())

            # Create a dictionary from the DataFrame row
            data_dict = df.iloc[-1].to_dict()

            # Save the data as JSON
            with open(f"data/{unique_id}.json", "w") as json_file:
                json.dump(data_dict, json_file)

            return f"Data saved as JSON with ID: {unique_id}"

    return ""


@app.callback(
    Output("output-div-backtest", "children"),
    Input("run-backtest-button", "n_clicks"),
)
def run_backtest(run_button_clicks):
    if run_button_clicks > 0:
        # Set the 'run_backtest' flag in the JSON file to true
        if not df.empty:
            data_dict = df.iloc[-1].to_dict()
            data_dict["run_backtest"] = True
            latest_json_file, _ = get_latest_json("data")
            latest_uuid = os.path.splitext(latest_json_file)[0]
            subprocess.call(["python", "momentum.py"])
            return f"Running backtest based on: {latest_uuid}"
        else:
            return "No parameters specified to run backtest on. Please save some data first."

    return ""


if __name__ == "__main__":
    app.run_server(debug=True)
