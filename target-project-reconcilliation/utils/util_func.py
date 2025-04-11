import json

from apis.pagination import next_page
from apis.rest_api import groups, group_orgs, org_targets, target_details

# Handle pagination
# Is the current org in scope?
def org_of_interest(orgs, orgname):
    if orgs == None or orgname in orgs:
        return True
    return False
