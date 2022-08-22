# List all issues (including Snyk Code) for a Snyk Organization

## Description

Use this script to get all the issues (including code issues) for a specific Snyk organization and then process the data

## Flow and Endpoints

- Call [API](https://snyk.docs.apiary.io/reference/projects/all-projects) to retrieve all projects ID
- For each project call get issues API from aggregated issues API and V3 (if "type": "sast")

**For no code projects**
    - [Get aggregated issues](https://snyk.docs.apiary.io/reference/projects/aggregated-project-issues/list-all-aggregated-issues)

**For code projects**
    - [Get aggregated code issues](https://apidocs.snyk.io/?version=2022-04-06%7Eexperimental#get-/orgs/-org_id-/issues)

- For each code issue enrich the data with the issues API
    - Loop for each issue with this [API call](https://apidocs.snyk.io/?version=2022-04-06%7Eexperimental#get-/orgs/-org_id-/issues/detail/code/-issue_id-)


- If issue is ignored call this [endpoint](https://snyk.docs.apiary.io/reference/projects/project-ignores-by-issue/retrieve-ignore) to get the ignore reason

## Code examples

Python:

[https://github.com/obenn/snyk-api-workshop](https://github.com/obenn/snyk-api-workshop)