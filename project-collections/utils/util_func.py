import json
import urllib.parse
import utils.rest_api


def next_page(response):
    # response['links']['next']
    try:
        pagination = urllib.parse.parse_qs(response['links']['next'],
                                           keep_blank_values=False, strict_parsing=False,
                                           encoding='utf-8', errors='replace',
                                           max_num_fields=None, separator='&')
        pagination = pagination['starting_after'][0]
    except:
        pagination = None
    return pagination



def build_collection(headers, args):
    # Retrieve all my groups
    g_response = json.loads(utils.rest_api.groups(headers, args["api_ver"]))

    # dictionary for all the issues within the tagged projects
    tp_issues = {}

    # Parse the list of tag values that identify projects of interest
    projects_of_interest = []
    tag_values = []
    tags = args["project_tags"].split(",")
    for tag in tags:
        tag_values.append(tag)

    # Iterate to the named group
    for group in g_response['data']:
        if group['attributes']['name'] == args['grp_name']:
            go_pagination = None
            while True:
                go_response = json.loads(utils.rest_api.group_orgs(headers, args["api_ver"], group, go_pagination))

                # Iterate to the named Org
                for org in go_response['data']:
                    if org['attributes']['name'] == args["org_name"]:

                        # Find the collection id
                        collection_id = find_collection(headers, args, org)
                        op_pagination = None
                        while True:
                            # Use of the project_tags ensures only those with the right tag are returned
                            op_response = json.loads(
                                utils.rest_api.org_projects(headers, args["api_ver"], org,
                                                            args["project_tags"], op_pagination))

                            for project in op_response['data']:
                                # iterate over the tags in each project and persist it i it has one of the tags
                                # of interest
                                utils.rest_api.add_project_to_collection(headers, args, org, collection_id, project)

                            # Next page?
                            op_pagination = next_page(op_response)
                            if op_pagination is None:
                                break

                # Next page?
                go_pagination = next_page(go_response)
                if go_pagination is None:
                    break


def find_collection(headers, args, org):
    collections = utils.rest_api.get_collections(headers, args["api_ver"], org)
    for coll in collections:
        if coll['attributes']['name'] == args["collection_name"]:
            return coll['id']
    return utils.rest_api.create_a_collection(headers, args, org)