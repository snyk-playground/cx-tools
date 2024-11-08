import json
import os
from apis.pagination import next_page
from apis.rest_api import groups, group_orgs, get_collections, create_a_collection



def process_collection(args, func):
    # Retrieve all my groups
    g_pagination = None

    while(True):
        g_response = json.loads(groups(g_pagination).text)

        try:
            # Iterate to the named group
            go_pagination = None
            for group in g_response['data']:
                if group['attributes']['name'] == args['grp_name']:
                    while True:
                        go_response = json.loads(group_orgs(group, go_pagination).text)

                        # Iterate to the named Org
                        for org in go_response['data']:
                            if org['attributes']['name'] == args["org_name"] or org['attributes']['slug'] == args["org_name"]:

                                # Find the collection id
                                collection_id = find_collection(args, org)

                                # Do the collection process within the passed function
                                func(args, org, collection_id)

                                # Now the named org has been processed, there's no need to continue
                                return

                        # Next page?
                        go_pagination = next_page(go_response)
                        if go_pagination is None:
                            break

        except Exception:
            print("GET call to /groups API returned no 'data'")
            print(json.dumps(g_response, indent=4))
            return

        g_pagination = next_page(g_response)
        if g_pagination is None:
            break


def find_collection(args, org):

    c_pagination = None
    collections = []
    response = None

    try:
        while True:
            response = json.loads(get_collections(org, c_pagination).text)
            collections = collections + response["data"]

            # Next page?
            c_pagination = next_page(response)
            if c_pagination is None:
                break

        for coll in collections:
            if coll['attributes']['name'] == args["collection_name"]:
                return coll['id']

        return create_a_collection(args, org)
    except Exception:
        print("GET call to /collections API returned no 'data'")
        print(json.dumps(response, indent=4))
        return


