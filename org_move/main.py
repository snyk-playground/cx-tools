import requests
import json
import argparse
import os

parser = argparse.ArgumentParser(description='startgroup: input the group id for which you would like to update all orgs within. endgroup: input the group id to which you would like the orgs to move. file: input the file path for your list of orgs. dryrun: y/n')
parser.add_argument("--startgroup")
parser.add_argument("--endgroup")
parser.add_argument("--file")
parser.add_argument("--dryrun")
args = parser.parse_args()
startgroup_id = args.startgroup
endgroup_id = args.endgroup
org_list = args.file
dryrun = args.dryrun

# Collect Snyk token if not in environment
if "SNYK_TOKEN" in os.environ:
    snyk_token = os.environ['SNYK_TOKEN']
else:
    print("Enter your Snyk API Token") 
    snyk_token = input()

# Collect Start Group ID if not provided during script call
if startgroup_id == '':
    print("Enter your Origin Group ID")
    startgroup_id = input()

# Collect End Group ID if not provided during script call
if endgroup_id == '':
    print("Enter your Destination Group ID")
    endgroup_id = input()

# Collect filepath if not provided during script call
if org_list == '':
    print("Enter your Org List filepath")
    org_list = input()

# Ensure Dryrun is set to y or n
if dryrun != 'y' and dryrun != 'n':
    print("Dryrun? Please enter y or n")
    dryrun = input()

# Open list of Orgs to move
with open(org_list, 'r') as file:
    orgs = file.read().splitlines()

# Loop through orgs and print their ID
for i in orgs:
    org_response = requests.get(f'https://api.snyk.io/rest/groups/{startgroup_id}/orgs?version=2024-06-21&slug={i}', headers={'Authorization': f'Token {snyk_token}'}).json()
    org_res = org_response['data']
    for org in org_res:
        org_id = org['id']
        if dryrun == 'y':
            print(f'Dryrun - This org will be moved! Org ID: {org_id}')
        else:
            print(f'Moving Org ID: {org_id}')
            headers = {'accept': 'application/vnd.api+json','authorization': f'token {snyk_token}','content-type': 'application/vnd.api+json'}
            data = {"data":{"attributes":{"parent_group_id":f"{endgroup_id}"},"type":"org_move"}}
            move_response = requests.post(f'https://api.snyk.io/rest/orgs/{org_id}/moves?version=2024-06-21%7Eexperimental', headers=headers, json=data).json()
            move_res = move_response['data']['attributes']['status']
            print(f'Move Response: {move_res}')
