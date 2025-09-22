import re

name = "abc"

if len(name) < 1 or len(name) > 200:
    raise ValueError("Metric name must be between 1 and 200 characters long")
metric_name_regex = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
print(metric_name_regex.match(name).match)
if metric_name_regex.match(name) == 0:
    raise ValueError
