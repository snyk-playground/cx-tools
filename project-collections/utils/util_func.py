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



def process_collection(headers, args, func):
    # Retrieve all my groups
    g_response = json.loads(utils.rest_api.groups(headers, args["api_ver"]))

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

                        # Do the collection process within the passed function
                        func(headers, args, org, collection_id)

                # Next page?
                go_pagination = next_page(go_response)
                if go_pagination is None:
                    break



def find_collection(headers, args, org):

    c_pagination = None
    collections = []

    while True:
        response = json.loads(utils.rest_api.get_collections(headers, args["api_ver"], org, c_pagination))
        collections = collections + response["data"]

        # Next page?
        c_pagination = next_page(response)
        if c_pagination is None:
            break

    for coll in response["data"]:
        if coll['attributes']['name'] == args["collection_name"]:
            return coll['id']

    return utils.rest_api.create_a_collection(headers, args, org)

