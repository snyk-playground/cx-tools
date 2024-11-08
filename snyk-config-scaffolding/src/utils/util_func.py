import json

from apis.pagination import next_page
from apis.rest_api import create_service_account, group_orgs, groups

def service_account_key(args, org, role_id):
    svc_ac_key = None
    response = create_service_account(org, role_id, args["org_service_account_name"])
    if response.status_code == 201:
        service_account_data = response.json()
        print('Service account {0} created successfully!'.format(service_account_data["data"]["attributes"]["name"]))
        svc_ac_key = service_account_data["data"]["attributes"]["api_key"]
    else:
        print(
            f"Failed to create service account {args['org_service_account_name']}: {response.status_code} - {response.text}")
    return svc_ac_key


# Check if the target organisation name already exists
def check_organization_exists(args, group_id):
    while True:
        pagination = None
        response = group_orgs(group_id, pagination)
        if response.status_code == 200:
            orgs = json.loads(response.text)['data']
            for org in orgs:
                if org['attributes']['name'] == args["org_name"]:
                    try:
                        if args["return"].upper() == "SLUG":
                            return org['attributes']['slug']
                    except:
                        pass
                    finally:
                        return org['id']
            pagination = next_page(json.loads(response.text))
            if pagination is None:
                return pagination


# Iterate over your groups and return the id for the required group name
def get_named_group(args):
    while True:
        pagination = None
        response = groups(pagination)
        if response.status_code == 200:
            my_groups = json.loads(response.text)['data']
            for group in my_groups:
                if group["attributes"]["name"] == args["group_name"]:
                    return group
            pagination = next_page(json.loads(response.text))
            if pagination is None:
                return pagination
