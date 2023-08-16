import dash
from dash import html, dcc
from dash import dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import html 
import pandas as pd
from process_json import get_latest_json
import subprocess
import os
import uuid
import json
from datetime import datetime, date
import numpy as np

test_experiment_JSON = "a7c6cca5-1634-4a3d-a95b-76311815f87a.json"

# Initialize the DataFrame
df = pd.DataFrame(
    columns=[
        "Experiment_Name",
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

# create experiment name
def get_experiment_name():
    # Format the current date and time as a string
    formatted_datetime = datetime.now().strftime("%H%M_%y%m%d")

    # Create the variable with the string "experiment" and the formatted datetime
    experiment_variable = f"experiment_{formatted_datetime}"
    return experiment_variable

# Function for "select experiment dropdown". Gets a dictionary with JSON filenames and corresponding Experiment_Names
def get_experiment_info():
    data_folder = 'data'  # Folder where JSON files are located
    experiment_info = {}
    for filename in os.listdir(data_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(data_folder, filename)
            with open(file_path, "r") as json_file:
                data_dict = json.load(json_file)
                experiment_name = data_dict.get("Experiment_Name")
                if experiment_name:
                    experiment_info[filename] = experiment_name

    # Sort the dictionary by the file modification time in descending order
    sorted_experiment_info = dict(sorted(experiment_info.items(), key=lambda item: os.path.getmtime(os.path.join(data_folder, item[0])), reverse=True))

    return sorted_experiment_info

# Function to get the first entry in experiment options
def get_latest_experiment_name_value(options):
    # Get the first key-value pair from the dictionary
    first_key, first_value = next(iter(options.items()))

    return first_key  # Return the latest experiment name

def get_experiment_info():
    data_folder = 'data'  # Folder where JSON files are located
    experiment_info = {}
    for filename in os.listdir(data_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(data_folder, filename)
            with open(file_path, "r") as json_file:
                data_dict = json.load(json_file)
                experiment_name = data_dict.get("Experiment_Name")
                if experiment_name:
                    experiment_info[filename] = experiment_name

    # Sort the dictionary by the file modification time in descending order
    sorted_experiment_info = dict(sorted(experiment_info.items(), key=lambda item: os.path.getmtime(os.path.join(data_folder, item[0])), reverse=True))

    return sorted_experiment_info

def load_initial_datatable():
    experiment_id = get_latest_experiment_name_value(get_experiment_info())
    experiment_id = experiment_id.replace(".json", "")

    # Fetch the data for the datatable here
    result_log_df = pd.read_csv("data/result_log.csv")

    result_log_df = result_log_df[result_log_df["experiment_id"] == experiment_id]
    

    # Convert the DataFrame to a dictionary format suitable for the DataTable
    data_dict = result_log_df.to_dict('records')

    return data_dict

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP]) # , suppress_callback_exceptions=True

app.layout = dbc.Container(
    [
        dbc.Row([dbc.Col(html.H1("🤖 Awesome Backtester"), className="mb-4 mt-4")]),
        dbc.Row([
                dbc.Col(
                    dbc.Input(id="experiment-name", value=get_experiment_name(), type="text", style={"width": "700px"}), 
                    width="auto"),                
        ],
        # align="center",
        # style={"margin-top": "10px", "margin-bottom": "20px", "margin-left": "0px", "margin-right": "50px"}
        ),
        dbc.Row([
                dbc.Col([
                        html.Label(
                            "Period: ", className="mt-4", style={"font-weight": "bold", "margin-right": "10px"}
                        ),
                        dcc.DatePickerRange(
                            id="date-range-selector",
                            start_date_placeholder_text= None, #start_date,
                            end_date_placeholder_text= None, #end_date,
                            calendar_orientation="horizontal",
                        ),
                    ],
                    width=4,
                ),
                dbc.Col(
                    [
                        html.Label(
                            "Starting Balance:",
                            className="mt-4",
                            style={"font-weight": "bold", "margin-right": "10px"},
                        ),
                        dbc.Input(
                            id="starting-balance-input",
                            type="number",
                            placeholder="Enter starting balance",
                            min=0,
                        ),
                    ],
                    width=4,
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
                            multi=True,
                        ),
                    ],
                    md=4,
                ),
            ],
            align="center",
        ),
        dbc.Row([
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
                            multi=True,
                        ),
                    ],
                    width=4,
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
                            multi=True,
                        ),
                    ],
                    width=4,
                ),
                dbc.Col(
                    [
                        html.Label(
                            "Holdings:", className="mt-4", style={"font-weight": "bold"}
                        ),
                        dcc.Dropdown(
                            id="holdings-dropdown",
                            options=[
                                {"label": str(i), "value": i} for i in range(1, 11)
                            ],
                            placeholder="Select number of holdings",
                            multi=True,
                        ),
                    ],
                    width=4,
                ),
            ],
            align="center",
        ),
        dbc.Row([
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
                            multi=True,
                        ),
                    ],
                    width=4,
                ),
            ],
            align="center",
        ),
        dbc.Row([
                dbc.Col(
                    [
                        dbc.Button(
                            "Run backtest",
                            id="run-backtest",
                            n_clicks=0,
                            color="primary",
                            className="mt-4 me-2",
                        ),
                    ],
                    width="auto",),
                dbc.Col(
                    [
                        dcc.Dropdown(
                            id="select-experiment",
                            options=get_experiment_info(),
                            value=get_latest_experiment_name_value(get_experiment_info()),
                            style={"width": "300px"},
                            clearable=False,
                        ),
                    ],
                    width="auto",
                    style={"width": "300px", "margin-top": "25px"},)
                ],
                align="center",
                style={"margin-bottom": "20px"},
            ),
        dbc.Row(
            [
                dbc.Col([html.Div(id="output-div", className="mt-4")]),
            ],
        ),
        dbc.Row( # id='datatable-experiments'
            [
                dbc.Col(
                    [
                        dash_table.DataTable(
                            id='datatable-experiments',
                            columns=[
                                {'name': 'run_id', 'id': 'run_id'},
                                {'name': 'Cumulative Return', 'id': 'Cumulative Return'},
                                {'name': 'Cagr', 'id': 'Cagr'},
                                {'name': 'Sharpe', 'id': 'Sharpe'},
                                {'name': 'Max Drawdown', 'id': 'Max Drawdown'},
                                {'name': 'experiment_id', 'id': 'experiment_id'}],
                            data=load_initial_datatable(),
                            filter_action='native',  # Add filtering option
                            sort_action='native',  # Add sorting option
                            sort_mode='multi',  # Allow multi-column sorting
                            page_size=10,  # Set the number of rows per page
                            row_selectable='single',  # Enable single row selection
                            selected_rows=[0],  # Automatically select the first row
                            style_as_list_view=True,
                            style_data={
                                'font-family': 'Arial, sans-serif',
                                'font-size': '16px',
                            },
                            style_cell={
                                #'textAlign': 'left',
                                'whiteSpace': 'normal',
                                'height': 'auto',
                            },
                            style_header={
                                #'textAlign': 'left',  # Align header cells to the left
                                'font-family': 'Arial, sans-serif',
                                'font-size': '16px',
                                'font-weight': 'bold',
                                'color': 'black',
                            },
                        ),                        
                    ],
                    style={"margin-bottom": "20px"}    
                ),
            ]
        ),        
        dbc.Row(
            [
            dbc.Tabs([
                dbc.Tab(label='Analysis', tab_id='analysis', children=[
                    html.Img(id="log-returns-plot"),
                    html.Img(id="drawdown-plot"),
                    html.Img(id="drawdown-periods-plot"),
                    html.Img(id="yearly-returns-plot"),
                    html.Img(id="monthly-heatmap-plot"),
                ]),
                dbc.Tab(label='Trade Log', tab_id='trade-log', children=[
                        dash_table.DataTable(
                            id='datatable-trades',
                            columns=[
                                {'name': 'unique_run_id', 'id': 'unique_run_id'},
                                {'name': 'Date', 'id': 'Date'},
                                {'name': 'Ticker', 'id': 'Ticker'},
                                {'name': 'Action', 'id': 'Action'},
                                {'name': 'Quantity', 'id': 'Quantity'},
                                {'name': 'Price', 'id': 'Price'},
                                {'name': 'PnL', 'id': 'PnL'},
                                {'name': 'cash_balance', 'id': 'cash_balance'},
                                #{'name': 'Timestamp', 'id': 'Timestamp'},
                                #{'name': 'unique_param_id', 'id': 'unique_param_id'},
                                #{'name': 'unique_experiment_id', 'id': 'unique_experiment_id'},
                            ],
                            data=[],
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            row_selectable='single',
                            selected_rows=[0],
                            sort_action='native',  # Add sorting option
                            filter_action='native', 
                            style_as_list_view=True,
                            style_data={
                                'font-family': 'Arial, sans-serif',
                                'font-size': '16px',
                            },
                            style_cell={
                                #'textAlign': 'left',
                                'whiteSpace': 'normal',
                                'height': 'auto',
                            },
                            style_header={
                                #'textAlign': 'left',  # Align header cells to the left
                                'font-family': 'Arial, sans-serif',
                                'font-size': '16px',
                                'font-weight': 'bold',
                                'color': 'black',
                            },
                        ),
                ]),
            ], id='tabs', active_tab='analysis'),
            html.Div(id="tabs-content")
            ],
            style={"margin-left": "0px"}
        ),
        dbc.Row(
            [
                html.Div(id="output-selected-row"),  # This div will display the selected row ID
            ]
        ),
    ],
    fluid=True,
)

# New callback to print selected row ID
@app.callback(
    Output("output-selected-row", "children"),
    Output("log-returns-plot", "src"),
    Output("drawdown-plot", "src"),
    Output("drawdown-periods-plot", "src"),
    Output("yearly-returns-plot", "src"),
    Output("monthly-heatmap-plot", "src"),
    Input("datatable-experiments", "selected_rows"),
    State("datatable-experiments", "data"),
)
def print_selected_row(selected_rows, data):
    if not data or len(data) == 0:
        return dash.no_update
    if selected_rows is not None and len(selected_rows) > 0:
        selected_row = data[selected_rows[0]] 
        log_return_plot_scr = f"assets\plots\{selected_row['experiment_id']}_{selected_row['run_id']}_log_returns.png"
        drawdown_plot_scr = f"assets\plots\{selected_row['experiment_id']}_{selected_row['run_id']}_drawdown.png"
        drawdown_periods_plot_scr = f"assets\plots\{selected_row['experiment_id']}_{selected_row['run_id']}_drawdown_periods.png"
        yearly_returns_plot_scr = f"assets\plots\{selected_row['experiment_id']}_{selected_row['run_id']}_yearly_returns.png"
        monthly_heatmap_scr = f"assets\plots\{selected_row['experiment_id']}_{selected_row['run_id']}_monthly_heatmap.png"
        print(f'log_return_plot_scr {log_return_plot_scr}')
        return (f"Selected Row ID: {selected_row['run_id']}", 
            log_return_plot_scr,
            drawdown_plot_scr,
            drawdown_periods_plot_scr,
            yearly_returns_plot_scr,
            monthly_heatmap_scr
            )
    else:
        return "No row selected."

# Save parameter and Run Backtest 
@app.callback(
    Output("output-div", "children"),
    Output("select-experiment", "options"),
    Output("select-experiment", "value"),
    Output("experiment-name", "value"),
    Output("date-range-selector", "start_date"),
    Output("date-range-selector", "end_date"),
    Output("starting-balance-input", "value"),
    Output("look-back-periods-dropdown", "value"),
    Output("skip-last-period-dropdown", "value"),
    Output("rebalancing-dropdown", "value"),
    Output("holdings-dropdown", "value"),
    Output("fee-per-trade-dropdown", "value"),
    Input("run-backtest", "n_clicks"),
    State("experiment-name", "value"),
    State("date-range-selector", "start_date"),
    State("date-range-selector", "end_date"),
    State("starting-balance-input", "value"),
    State("look-back-periods-dropdown", "value"),
    State("skip-last-period-dropdown", "value"),
    State("rebalancing-dropdown", "value"),
    State("holdings-dropdown", "value"),
    State("fee-per-trade-dropdown", "value"),
)
def update_output(
    n_clicks_save,
    experiment_name,
    start_date,
    end_date,
    starting_balance,
    look_back_periods,
    skip_last_period,
    rebalancing,
    holdings,
    fee_per_trade,
):
    if n_clicks_save > 0:
        # if experiment_name is None:
        #     return "Please enter experiment name", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        if start_date is None or end_date is None:
            return "Please select a start date and an end date", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        elif starting_balance is None:
            return "Please enter a starting balance", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        elif look_back_periods is None:
            return "Please select look back periods", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        elif skip_last_period is None:
            return "Please select skip last period", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        elif rebalancing is None:
            return "Please select a rebalancing period", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        elif holdings is None:
            return "Please select number of holdings", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        elif fee_per_trade is None:
            return "Please select fee per trade", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        else:
            # Create a dictionary with the user's input data
            data_dict = {
                "Experiment_Name": experiment_name,
                "Start_Date": start_date,
                "End_Date": end_date,
                "Starting_Balance": starting_balance,
                "Look_Back_Periods": look_back_periods,
                "Skip_Last_Period": skip_last_period,
                "Rebalancing": rebalancing,
                "Holdings": holdings,
                "Fee_Per_Trade": fee_per_trade,
                "run_backtest": True,
            }

            # Generate a unique ID for the JSON file
            unique_id = str(uuid.uuid4())

            # Save the data as JSON
            data_folder = "data"
            json_file_path = os.path.join(data_folder, f"{unique_id}.json")
            with open(json_file_path, "w") as json_file:
                json.dump(data_dict, json_file)

            # TIGGER BT. BRING BACK IN ONCE PROD

            # if df.shape[0] > 1:
            #     subprocess.call(["python", "gridsearch.py"])
            # else:
            #     subprocess.call(["python", "momentum.py"])

            # Get updated options for select-experiment dropdown
            updated_options = get_experiment_info()

            # Select latest experiment name und experiment selection dropdown
            lastest_experiment_name=get_latest_experiment_name_value(updated_options)

            # Reset parameters
            experiment_name = get_experiment_name()
            start_date_placeholder = "start"
            end_date_placeholder = "end"
            starting_balance_value = None
            look_back_periods_value = None
            skip_last_period_value = None
            rebalancing_value = None
            holdings_value = None
            fee_per_trade_value = None

            return (
                f"Data saved as JSON with ID: {unique_id} number of clicks: {n_clicks_save}", 
                updated_options, 
                lastest_experiment_name,
                experiment_name, 
                None, 
                None, 
                starting_balance_value, 
                look_back_periods_value, 
                skip_last_period_value, 
                rebalancing_value, 
                holdings_value, 
                fee_per_trade_value)

    return "", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# Create datatable for experiments
@app.callback(
    Output("datatable-experiments", "data"),
    Input("select-experiment", "value")
)
def update_output(experiment_id):
    experiment_id = experiment_id.replace(".json", "")
    result_log_df = pd.read_csv("data/result_log.csv")
    filtered_df = result_log_df[result_log_df["experiment_id"] == experiment_id]
    # print(f'filtered_df {filtered_df}')
    # print(f'filtered_df {filtered_df.columns}')
    # filtered_df['id'] = filtered_df['run_id']
    # filtered_df.set_index('id', inplace=True, drop=False)
    filtered_df = filtered_df.to_dict('records')
    # data1 = filtered_df[["id", "Cumulative Return", "Sharpe", "Max Drawdown", "experiment_id"]]
    # print(data)
    # datatable = dash_table.DataTable(
    #     id='datatable',
    #     columns=[{"name": col, "id": col} for col in data1.columns],
    #     data=filtered_df.to_dict('records'),
    #     filter_action='native',  # Add filtering option
    #     sort_action='native',  # Add sorting option
    #     sort_mode='multi',  # Allow multi-column sorting
    #     page_size=10,  # Set the number of rows per page
    #     row_selectable='single',  # Enable single row selection
    #     selected_rows=[0],  # Automatically select the first row
    #     style_as_list_view=True,
    #     style_data={
    #         'font-family': 'Arial, sans-serif',
    #         'font-size': '16px',
    #     },
    #     style_cell={
    #         #'textAlign': 'left',
    #         'whiteSpace': 'normal',
    #         'height': 'auto',
    #     },
    #     style_header={
            #'textAlign': 'left',  # Align header cells to the left
    #         'font-family': 'Arial, sans-serif',
    #         'font-size': '16px',
    #         'font-weight': 'bold',
    #         'color': 'black',
    #     }
    # )
    return filtered_df

# @app.callback(
#     # Output("div-output", "children"),
#     Output('datatable-trades', "data"),
#     Input("datatable-experiments", "selected_rows"),
#     State("datatable-experiments", "data")
# )
# def print_selected_row(selected_rows, table_data):                
#     print(f'selected_rows {selected_rows}')
#     selected_run_id = table_data[selected_rows[0]]['run_id'] # get run_id from the selected row of the dataTable. Single selection is must
#     print(f'selected_run_id {selected_run_id}')

#     file_path = r'data\trade_log.csv'
#     df_tradeLog = pd.read_csv(file_path)
#     df_filtered = df_tradeLog[df_tradeLog['unique_run_id'] == selected_run_id]
#     print(f'df_tradeLog {df_tradeLog.tail(10)}')
#     print(f'df_filtered {df_filtered.head(10)}')
#     data = df_filtered.to_dict('records')


    return selected_run_id, data

# Update datatable-trades on selection of experiment
@app.callback(
    Output('datatable-trades', "data"),
    Input("datatable-experiments", "selected_rows"),
    State("datatable-experiments", "data")
)
def print_selected_row(selected_rows, table_data):                
    selected_run_id = table_data[selected_rows[0]]['run_id'] # get run_id from the selected row of the dataTable. Single selection is must
    #print(f'selected_run_id {selected_run_id}')
    #print(f'table_data {table_data}')
    file_path = r'data\trade_log.csv'
    df_tradeLog = pd.read_csv(file_path)
    df_filtered = df_tradeLog[df_tradeLog['unique_run_id'] == selected_run_id]
    #print(f'df_tradeLog {df_tradeLog.tail(10)}')
    #print(f'df_filtered {df_filtered.head(10)}')
    data = df_filtered.to_dict('records')

    return data            

if __name__ == "__main__":
    app.run_server(debug=True, port=8001)