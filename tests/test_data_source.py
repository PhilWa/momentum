import pytest
from utils.utils import get_data


def test_column_compatibility_w_yfinance():
    col_comp = (
        get_data("AAPL", "2022-01-01", "2022-01-31", "db").columns
        == get_data("AAPL", "2022-01-01", "2022-01-31", "yahoo").columns
    )
    assert all(col_comp), "Columns are not the same"


def test_get_data_returns_dataframe():
    assert (
        get_data("AAPL", "2022-01-01", "2022-01-31", "db").empty == False
    ), "Dataframe is empty"


def test_get_data_returns_dataframe_with_correct_columns():
    assert get_data("AAPL", "2022-01-01", "2022-01-31", "yahoo").columns.to_list() == [
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume",
    ], "Columns are not the same"
