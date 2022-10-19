# Find all projects affected by a vuln

## Description

Use this script to find all your Snyk projects that are affected by a certain vuln

## Flow and Endpoints

### Flow

- Get the list of all organization IDs
- Aggregate the paginated results
- Slice the list of organizations into groups
- For each group of organizations
    - For each CVE
        - Get the list of issues using the reporting API
        - For each issue, extract the “projects” elements of the response to create links to the affected manifests
- Since branch name is needed for a direct SCM link, we need to get all projects using and extract the remoteRepoUrl and Branch
- Dedup results
- Convert list to CSV

### APIs used

- [Get a filtered list of issues](https://snyk.docs.apiary.io/#reference/reporting-api/issues/get-list-of-issues)
- [Get the organization IDs to feed to the reporting API call above](https://snyk.docs.apiary.io/#reference/groups/list-all-organizations-in-a-group/list-all-organizations-in-a-group)
- [Get all projects to construct proper links to SCM, including branch name](https://snyk.docs.apiary.io/#reference/projects/all-projects/list-all-projects)
