import json
import urllib.parse
import utils.rest_api
import utils.snyk_api


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

def org_of_interest(orgs, orgname):
    if orgs == None or orgname in orgs:
        return True
    return False



def parse_users(headers, args):
    # Retrieve all my groups
    g_response = json.loads(utils.rest_api.groups(headers, args["api_ver"]))
    orgs_members = dict()

    try:
        # Iterate to the named group
        for group in g_response['data']:
            if group['attributes']['name'] == args['grp_name']:
                go_pagination = None
                while True:
                    go_response = json.loads(utils.rest_api.group_orgs(headers, args["api_ver"], group, go_pagination))

                    # Iterate to the named Org
                    for org in go_response['data']:
                        if org_of_interest(args["org_names"], org['attributes']['name']):

                            # Parse the users
                            scoped_members = []
                            all_members = json.loads(utils.snyk_api.org_members(headers, org['id']))
                            for member in all_members:
                                if member['role'] in args['roles']:
                                    scoped_members.append(member)
                            orgs_members[org['attributes']['name']]=scoped_members

                    # Next page?
                    go_pagination = next_page(go_response)
                    if go_pagination is None:
                        break

        print(json.dumps(orgs_members, indent=4))


    except UnboundLocalError as err:
        print(err)
        print("GET call to /groups API returned no 'data'")
        print(json.dumps(g_response, indent=4))
        return


