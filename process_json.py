import os
import json
from datetime import datetime, timedelta
import re


def get_latest_json(dir_path: str) -> str:
    """Get the path of the most recently modified .json file."""
    # Get a list of all .json files in the directory.
    json_files = [f for f in os.listdir(dir_path) if f.endswith(".json")]

    # Sort the files by modification time.
    json_files.sort(key=lambda f: os.path.getmtime(os.path.join(dir_path, f)))

    # Get the path of the most recently modified .json file.
    latest_json_file = os.path.join(dir_path, json_files[-1])
    return latest_json_file, json_files[-1]


def load_json(str_path: str) -> dict:
    """Load the .json file at the given path."""
    with open(str_path, "r") as f:
        data = json.load(f)
    return data


def get_date(date_str: str):
    """Modify the given date by the given number of days."""
    return date_str


def check_for_number(data, number_type: str):
    """Check if input is of the specified number type (int or float)."""
    if number_type == "int":
        if isinstance(data, int):
            return data
        else:
            raise ValueError("Input does not contain an integer.")
    elif number_type == "float":
        if isinstance(data, float):
            return data
        else:
            raise ValueError("Input does not contain a float.")
    else:
        raise ValueError('Invalid number type. Must be "int" or "float".')


def split_into_time_and_period(data_str: str) -> dict:
    """Curate the look back period."""
    if not any(char in data_str for char in ["m", "d", "y"]):
        return ValueError('Input not valid. Must contain "m", "d", or "y".')

    # Get the number of days, months, and years.
    match = re.match(r"(\d+)(\D+)", data_str, re.I)
    if match:
        items = match.groups()
        return (int(items[0]), items[1])
    else:
        ValueError("Something went wrong.")


def curate_skip_last_period(data_str: str) -> bool:
    return True if data_str == "no" else False if data_str == "yes" else None


def modify_data(data: dict) -> dict:
    """Modify the fields in the data."""
    data["Start_Date"] = get_date(data["Start_Date"])
    data["End_Date"] = get_date(data["End_Date"])
    data["Starting_Balance"] = check_for_number(data["Starting_Balance"], "int")
    data["Look_Back_Periods"] = split_into_time_and_period(data["Look_Back_Periods"])
    data["Skip_Last_Period"] = curate_skip_last_period(data["Skip_Last_Period"])
    data["Rebalancing"] = split_into_time_and_period(data["Rebalancing"])
    data["Holdings"] = check_for_number(data["Holdings"], "int")
    data["Fee_Per_Trade"] = check_for_number(data["Fee_Per_Trade"], "int")
    return data


def get_params(dir: str = "data") -> dict:
    # Get the path of the most recently modified .json file.
    latest_json_file, fname = get_latest_json(dir)

    # Load the .json file at the given path.
    data = load_json(latest_json_file)

    # Modify the fields in the data.
    data = modify_data(data)

    # Output the modified data.
    return data, os.path.splitext(fname)[0]


print(get_params())
