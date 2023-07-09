import subprocess
from tqdm import tqdm
import json
import itertools
import uuid
from datetime import datetime


def create_parameter_combinations(param_dict):
    keys, values = zip(*param_dict.items())
    combinations_dicts = [dict(zip(keys, v)) for v in itertools.product(*values)]
    return combinations_dicts


# This is a dummy version of the parameters that would be passed in from the JSON file.
# Here the question is how we want to come up with the gridsearch params
params_json = """
{
    "Start_Date": ["2022-01-01"],
    "End_Date": ["2022-12-31"],
    "Starting_Balance": [100000],
    "Look_Back_Periods": ["12m", "5m"],
    "Skip_Last_Period": ["yes","no"],
    "Rebalancing": ["1m"],
    "Holdings": [2,3],
    "Fee_Per_Trade": [1]
}
"""
params_dict = json.loads(params_json)
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
    command = ["python", "analyze_trade_log.py"]
    subprocess.run(command, shell=False, capture_output=False)
print("Time taken: ", datetime.now() - start_time)
