import argparse
import json
import os

from apis.pagination import next_page
from apis.rest_api import org_projects, add_project_to_collection, get_collection_projects, \
    delete_project_from_collection
from utils.util_func import process_collection

# List for collection projects to be held, pending lookup with projects that contain the search tag
collection_projects = []

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


def is_project_in_collection(org_id, project_id, collection_id):
    global collection_projects
    if not collection_projects:
        coll_pagination = None
        while True:
            response = json.loads(get_collection_projects(org_id, collection_id, coll_pagination).text)
            for rel in response["data"]:
                # Save the id of the target that owns the project within the collection
                # The api doesn't return the project id per-se, so the target is the best available reference
                collection_projects.append(rel["id"])

            # Add a dummy entry to ensure the empty collection does not cause the collection projects
            # list to be retrieved next time
            if not collection_projects:
                collection_projects.append("Dummy")

            # Next page?
            coll_pagination = next_page(response)
            if coll_pagination is None:
                break


    # Is the project already in the collection
    if project_id in collection_projects:
        # Remove the accounted for project. By the end projects that remain are no longer aligned to the list
        # of projects with the tag and should be removed from the collection
        collection_projects.remove(project_id)
        return True
    return False


def build_collection(args, org, collection_id):
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
                if is_project_in_collection(org["id"], project["id"], collection_id) is False:
                    add_project_to_collection(org, collection_id, project["id"])

            # Next page?
            op_pagination = next_page(op_response)
            if op_pagination is None:
                break

        # Remove the dummy id that prevented the empty collection yielding another parse of the
        # collection content once the first item was added to the collection
        if collection_projects.__contains__("Dummy"):
            collection_projects.remove("Dummy")

        # Any project ids from list that made up the collection which have not been deleted
        # no longer return in the 'tagged' projects list and therefore must be deleted from
        # the collection
        for project_id in collection_projects:
            delete_project_from_collection(org, collection_id, project_id)

    except Exception:
        print("POST call to /collections - Unable to build collection")
        print(json.dumps(op_response, indent=4))
        return




# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    args = get_arguments()
    process_collection(args, build_collection)


