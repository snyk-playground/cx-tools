import argparse
import os

from utils.util_func import service_account_key, check_organization_exists, get_named_group
from apis.snyk_api import get_group_role_id, create_organization


# Parse command line arguments that instruct program operation
def get_arguments():
    parser = argparse.ArgumentParser(
        description='This script enables Snyk customers to scaffold configuation for projects from within their \
        CD-CD pipelines')
    parser.add_argument('-g', '--group_name', required=True)
    parser.add_argument('-a', '--group_svc_ac_token', required=True)
    parser.add_argument('-r', '--group_role_name', required=True)
    parser.add_argument('-o', '--org_name', required=True)
    parser.add_argument('-s', '--org_service_account_name', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-08-15")
    parser.add_argument('-t', '--template_org_id', default=None)
    args = vars(parser.parse_args())
    if args["group_svc_ac_token"]:
        os.environ["SNYK_TOKEN"] = args["group_svc_ac_token"]
    os.environ["API_VERSION"] = args["api_ver"]

    return args


# Build the named org, service account assigned to the named group role and return the service account auth token upon
# creation only. You must store the key securely within your environment for use by pipelines to commit to the created
# organisation.
def scaffold_snyk_config(args):
    svc_ac_key = None
    group = get_named_group(args)
    if group is not None:
        org_id = check_organization_exists(args, group)
        role_id = get_group_role_id(args, group, args["group_role_name"])
        if org_id is None:
            response = create_organization(args, group)
            if response.status_code == 201:
                org = response.json()
                print('Organisation {0} created successfully!'.format(org["name"]))
                svc_ac_key = service_account_key(args, org["id"], role_id)

            else:
                print(f"Failed to create organisation: {response.status_code} - {response.text}")
        else:
            svc_ac_key = service_account_key(args, org_id, role_id)
    return svc_ac_key


# Main function
if __name__ == '__main__':
    args = get_arguments()
    key = scaffold_snyk_config(args)
    exit(key)
