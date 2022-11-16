#!/bin/bash
# the first argument is the script name to be ran as <script-name>/cli.py

# the rest of the arguments can be applied as-is
python /app/snyk_code_ci_check.py "${@}"
