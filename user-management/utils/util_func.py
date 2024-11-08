import json
import urllib.parse

from apis.pagination import next_page
from apis.rest_api import groups, group_orgs
from apis.snyk_api import org_members


def org_of_interest(orgs, orgname):
    if orgs == None or orgname in orgs:
        return True
    return False



def parse_users(args):
    # Retrieve all my groups
    g_pagination = None
    while True:
        g_response = json.loads(groups(g_pagination).text)
        orgs_members = dict()

        try:
            # Iterate to the named group
            for group in g_response['data']:
                if group['attributes']['name'] == args['grp_name']:
                    go_pagination = None
                    while True:
                        go_response = json.loads(group_orgs(group, go_pagination).text)

                        # Iterate to the named Org
                        for org in go_response['data']:
                            if org_of_interest(args["org_names"], org['attributes']['name']):

                                # Parse the users
                                scoped_members = []
                                all_members = json.loads(org_members(org['id']).text)
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

        g_pagination = next_page(g_response)
        if g_pagination is None:
            break


