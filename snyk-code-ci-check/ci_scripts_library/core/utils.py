# utilities
import json
import re
import time

from typing import Dict, List
from datetime import datetime
from ci_scripts_library.core import SuperSnykClient
from ci_scripts_library.core.snyk_models import ProjectIssues
from snyk.models import Project, AggregatedIssue
import pprint

def get_repo_full_name_from_repo_url(repo_url:str) -> str:
    repo_name = None
    match = re.search('.+://.+/(.+/.+)\.git', repo_url)
    if match:
        repo_name = match.group(1)
    else:
        match = re.search('.+://.+/(.+/.+)',repo_url)
        if match:
            repo_name = match.group(1)
        else:
            repo_name = "<repo not detected>"

    return repo_name    


# Get Snyk org for the specified org slug
def get_snyk_org_from_slug(snyk_client:SuperSnykClient, org_slug: str):
    snyk_org_slug = org_slug
    try:
        snyk_orgs = snyk_client.organizations.all()
    except:
        return None

    snyk_org = [x for x in snyk_orgs if f"{snyk_org_slug}" == x.attributes['slug']]
    if len(snyk_org) > 0:
        return snyk_org[0]
    else:
        return None


def is_snyk_project_fresh(last_tested_date: str):

    current_time = datetime.utcnow()

    last_tested = datetime.strptime(last_tested_date, '%Y-%m-%dT%H:%M:%S.%fZ')
    total_time = (current_time - last_tested).total_seconds()
    #print(f"seconds since last_tested: {total_time=}")

    if total_time < 600:
        return True
    else:
        return False

def get_snyk_code_project_for_repo_target(snyk_client:SuperSnykClient, snyk_org_id, gh_repo_full_name):

#    print(f"{gh_repo_full_name=}")
    filter_for_snyk_projects = {  
        "filters": {
           "type": "sast",
        }
    }

    try:
        snyk_client.v1_client.post(f"/org/{snyk_org_id}/projects", filter_for_snyk_projects)
        projects:List[Project] = snyk_client.v1_client.post(f"/org/{snyk_org_id}/projects", filter_for_snyk_projects).json()

        projects = [x for x in projects['projects'] if x['name'] == gh_repo_full_name]
        return projects
    except:
        return None

def get_snyk_org_id(snyk_client:SuperSnykClient, org_slug: str, org_id: str):
    org = None

    if org_id:
        org = org_id
    elif org_slug:
        try:
            org = get_snyk_org_from_slug(snyk_client, org_slug).id
        except:
            org = None
    else:
        org = None

    return org