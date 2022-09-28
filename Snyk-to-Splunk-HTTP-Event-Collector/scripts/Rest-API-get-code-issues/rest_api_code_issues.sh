#!/bin/bash

# LOW SEVERITY ISSUES
# get code results with the API
curl --request GET "https://api.snyk.io/rest/orgs/3ee0d99d-1651-4b78-b9a4-a2658bd1815e/issues?project_id=7107beaa-3011-4821-bb2a-bb0e4226b731&severity=low&type=code&version=2022-04-06%7Eexperimental" \
--header "Accept: application/vnd.api+json" \
--header "Authorization: Token <Your Snyk Token>" | tee code_results_low.json

# We can also leverage the python script: easier to configure
#pip3 install -r requirements.txt
#python3 rest-get-code-issues.py 2>&1 | sed '1,5d;$d' | sed '$d' | tee asd.json

# create a post request - send the results to AWS Lambda
curl --location --request POST 'https://vxy2zw7203.execute-api.us-west-2.amazonaws.com/default/SplunkOfficial' \
--header 'Content-Type: application/json' \
--data @code_results_low.json

# MEDIUM SEVERITY ISSUES
curl --request GET "https://api.snyk.io/rest/orgs/3ee0d99d-1651-4b78-b9a4-a2658bd1815e/issues?project_id=7107beaa-3011-4821-bb2a-bb0e4226b731&severity=medium&type=code&version=2022-04-06%7Eexperimental" \
--header "Accept: application/vnd.api+json" \
--header "Authorization: Token <Your Snyk Token>" | tee code_results_med.json

curl --location --request POST 'https://vxy2zw7203.execute-api.us-west-2.amazonaws.com/default/SplunkOfficial' \
--header 'Content-Type: application/json' \
--data @code_results_med.json

# HIGH SEVERITY ISSUES
curl --request GET "https://api.snyk.io/rest/orgs/3ee0d99d-1651-4b78-b9a4-a2658bd1815e/issues?project_id=7107beaa-3011-4821-bb2a-bb0e4226b731&severity=high&type=code&version=2022-04-06%7Eexperimental" \
--header "Accept: application/vnd.api+json" \
--header "Authorization: Token <Your Snyk Token>" | tee code_results_high.json

curl --location --request POST 'https://vxy2zw7203.execute-api.us-west-2.amazonaws.com/default/SplunkOfficial' \
--header 'Content-Type: application/json' \
--data @code_results_high.json
