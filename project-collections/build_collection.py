import argparse
import json
import os

from apis.pagination import next_page
from apis.rest_api import org_projects, add_project_to_collection
from utils.util_func import process_collection

def get_arguments():
    parser = argparse.ArgumentParser(description='This script enables you to configure IQ Server from JSON\
     data, thus supporting the config-as-code requirement of Sonatype customers')
    parser.add_argument('-a', '--snyk_token', default=None)
    parser.add_argument('-g', '--grp_name', required=True)
    parser.add_argument('-o', '--org_name', required=True)
    parser.add_argument('-c', '--collection_name', required=True)
    parser.add_argument('-t', '--project_tags', required=True)
    parser.add_argument('-v', '--api_ver', default="2024-01-23")

    args = vars(parser.parse_args())
    if args["snyk_token"]:
        os.environ["SNYK_TOKEN"] = args["snyk_token"]
    os.environ["API_VERSION"] = args["api_ver"]
    return args


def is_project_in_collection(project):
    return False


def add_proj_to_collection(args, org, collection_id):
    op_pagination = None
    op_response = None
    try:
        while True:
            # Use of the project_tags ensures only those with the right tag are returned
            op_response = json.loads(
                org_projects(org,
                             args["project_tags"], op_pagination).text)

            for project in op_response['data']:
                # iterate over the tags in each project and persist it if it has one of the tags
                # of interest that does not exist already in the collection
                if is_project_in_collection(project) is False:
                    add_project_to_collection(org, collection_id, project)

            # Next page?
            op_pagination = next_page(op_response)
            if op_pagination is None:
                break
    except Exception:
        print("POST call to /collections - Unable to build collection")
        print(json.dumps(op_response, indent=4))
        return




# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    args = get_arguments()
    process_collection(args, add_proj_to_collection)


