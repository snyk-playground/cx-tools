# Retrieve a project snapshot for every project in a given Group

## Description

Use this script to fetch projects snapshots and use that data, for example: create custom reports with this data internally.

## Flow and Endpoints

1. [Get all orgs in a Group](https://snyk.docs.apiary.io/#reference/groups/list-all-organizations-in-a-group/list-all-organizations-in-a-group)
2. Returns array of org information
3. Create a new array of all orgIDs. Use org IDs
4. [Use new array and send as body with the get issues api call](https://snyk.docs.apiary.io/#reference/reporting-api/latest-issues/get-list-of-latest-issues)
5. Go through all pages to get the final data

## Code examples

(Python)
```Python
from pprint import pprint
import requests
AUTH_HEADER = {'Authorization': 'token ${SNYK_TOKEN}'}
GROUP_ID = ${SNYK_GROUP_ID}
print('Fetching orgs for group_id {group_id}'.format(group_id=GROUP_ID))
# TODO: there are more than 100 orgs (pagination)
r = requests.get('https://snyk.io/api/v1/group/{group_id}/orgs'.format(group_id=GROUP_ID),
                 headers=AUTH_HEADER)
orgs = r.json()['orgs']
for org in orgs:
    org_id = org['id']
    print('  Fetching projects for org_id {org_id} ({name})'.format(
        org_id=org_id, name=org['name']))
    r = requests.get(
        'https://snyk.io/api/v1/org/{org_id}/projects'.format(org_id=org_id), headers=AUTH_HEADER)
    projects = r.json()['projects']
    for project in projects:
        project_id = project['id']
        print('    Fetching snapshots for project_id {project_id} ({name})'.format(
            project_id=project_id, name=project['name']))
        r = requests.post('https://snyk.io/api/v1/org/{org_id}/project/{project_id}/history?perPage=1&page=1'.format(
            org_id=org_id, project_id=project_id), headers=AUTH_HEADER)
        snapshot = r.json()['snapshots'][0]
        pprint(snapshot)
        snapshot_id = snapshot['id']
        print('      Fetching aggregated issues for snapshot_id {snapshot_id}'.format(
            snapshot_id=snapshot_id))
        r = requests.post('https://snyk.io/api/v1/org/{org_id}/project/{project_id}/history/{snapshot_id}/aggregated-issues'.format(
            org_id=org_id, project_id=project_id, snapshot_id=snapshot_id), headers=AUTH_HEADER)
        pprint(r.json())
```