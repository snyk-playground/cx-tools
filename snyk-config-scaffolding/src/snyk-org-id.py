import argparse
import os

from utils.util_func import check_organization_exists, get_named_group


# Parse command line arguments that instruct program operation
def get_arguments():
    parser = argparse.ArgumentParser(
        description='This script enables Snyk customers to scaffold configuration for projects from within their \
        CD-CD pipelines')
    parser.add_argument('-g', '--group_name', required=True)
    parser.add_argument('-o', '--org_name', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-08-15")
    parser.add_argument('-r', '--return', default="ID")
    args = vars(parser.parse_args())
    os.environ["API_VERSION"] = args["api_ver"]

    return args


# Build the named org, service account assigned to the named group role and return the service account auth token upon
# creation only. You must store the key securely within your environment for use by pipelines to commit to the created
# organisation.
def snyk_org_id(args):
    svc_ac_key = None
    group_id = get_named_group(args)
    if group_id is not None:
        org_id = check_organization_exists(args, group_id)
    return org_id


# Main function
if __name__ == '__main__':
    args = get_arguments()
    org_id = snyk_org_id(args)
    exit(org_id)
