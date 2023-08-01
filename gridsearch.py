import subprocess
from tqdm import tqdm
import json
import uuid
from datetime import datetime
from utils import create_parameter_combinations
import argparse
from process_json import get_latest_json, load_json
import itertools

parser = argparse.ArgumentParser(description="Run gridsearch based on JSON file")
parser.add_argument(
    "-g", "--grid", default=False, type=bool, help="Activate grid search"
)
parser.add_argument(
    "-d", "--default", default=True, type=bool, help="Run in default mode"
)
args = parser.parse_args()

if args.default:
    pass
    # This is a dummy version of the parameters that would be passed in from the JSON file.
    # Here the question is how we want to come up with the gridsearch params
params_json = """
{
    "Start_Date": ["2015-01-01"],
    "End_Date": ["2022-12-31"],
    "Starting_Balance": [100000],
    "Look_Back_Periods": ["12m", "9m", "6m"],
    "Skip_Last_Period": ["yes","no"],
    "Rebalancing": ["1m", "3m", "6m"],
    "Holdings": [2,3,6],
    "Fee_Per_Trade": [1]
}
"""
params_dict = json.loads(params_json)


def create_parameter_combinations(param_dict: dict[str, list]) -> dict[str]:
    keys, values = zip(*param_dict.items())
    combinations_dicts = [dict(zip(keys, v)) for v in itertools.product(*values)]
    return combinations_dicts


# params_dict = get_latest_json("data")
parameters = create_parameter_combinations(params_dict)

start_time = datetime.now()
experiment_id = str(uuid.uuid4())
for parameter in tqdm(parameters):
    parameter["experiment_id"] = experiment_id
    run_id = str(uuid.uuid4())
    with open(f"data/{run_id}.json", "w") as f:
        json.dump(parameter, f, indent=4)
    command = ["python", "momentum.py", "--grid", "False"]
    subprocess.run(command, shell=False, capture_output=False)
    command = ["python", "analyze.py"]
    subprocess.run(command, shell=False, capture_output=False)
print("Time taken: ", datetime.now() - start_time)
