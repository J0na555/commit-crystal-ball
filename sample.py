"""Sample file for manually testing crystal-ball scan.

Run:          crystal-ball scan sample.py
With tone:    crystal-ball scan --tone horror sample.py

Each section below triggers a specific detector.
"""

import subprocess
import yaml
import requests

# --- eval_exec_usage: eval/exec/compile ---
result = eval("1 + 1")

# --- sql_injection: string formatting in execute ---
cursor = None  # placeholder
user_id = "123"
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")


# --- unsafe_yaml_load: yaml.load() without Loader ---
data = yaml.load(open("config.yaml"))

# --- missing_timeout: requests without timeout ---
response = requests.get("https://example.com")
