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

def load_json_file(json_file_path: str) -> Dict:
    """ return a JSON object as dictionary"""
    f = open(json_file_path)
    data = json.load(f)
    f.close()

    return data

def construct_vulndb_url(snyk_vuln_id: str) -> str:
    """ return a link to snyk's vulndb entry for given vuln ID"""
    return f"https://security.snyk.io/vuln/{snyk_vuln_id}"

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


def get_github_org_name(repo_url:str) -> str:
    try:
        repo_full_name = get_repo_full_name_from_repo_url(repo_url)
        github_org = repo_full_name.split("/")
        return github_org[0]
    except Exception as e:
        print(e)       

# Parse GitHub repo name from GitHub repo full name 
def get_github_repo_name(repo_url:str) -> str:
    try:
        repo_full_name = get_repo_full_name_from_repo_url(repo_url)
        github_repo = repo_full_name.split("/")
        return github_repo[1]
    except:
        print(f"The following remote repo: {repo_url} is invalid")

# Return snyk organizations that match Github Organizations with Snyk rest api
def find_snyk_org_from_github_org(snyk_client:SuperSnykClient, github_org_name: str, snyk_prefix: str):
    snyk_org_slug = github_org_name
    snyk_orgs = snyk_client.organizations.all()

    if snyk_prefix:
        snyk_org_slug = f"{snyk_prefix}_{github_org_name}"
    
    snyk_org = [x for x in snyk_orgs if f"{snyk_org_slug}" == x.attributes['slug']]
    if len(snyk_org) > 0:
        return snyk_org[0]
    else:
        return None

# Get Snyk org for the specified org slug
def get_snyk_org_from_slug(snyk_client:SuperSnykClient, org_slug: str):
    snyk_org_slug = org_slug
    snyk_orgs = snyk_client.organizations.all()

    snyk_org = [x for x in snyk_orgs if f"{snyk_org_slug}" == x.attributes['slug']]
    if len(snyk_org) > 0:
        return snyk_org[0]
    else:
        return None

# Return snyk organizations that match Github Organizations with Snyk rest api CLEAN UP
def find_github_repo_in_snyk(github_repo_name: str, snyk_projects):
    return [x for x in snyk_projects if github_repo_name == x.attributes.name]

def get_snyk_project_issues(snyk_client:SuperSnykClient, snyk_org, project_id):
    snyk_issues_filter = { "includeDescription": True, "filters":  { "types": ["vuln"], "ignored": False }  }

    #aggregated_issues:List[AggregatedIssue] = snyk_client.v1_client.post(f"/org/{snyk_org.id}/project/{project_id}/aggregated-issues", body=snyk_issues_filter).json()
    aggregated_issues = snyk_client.v1_client.post(f"/org/{snyk_org.id}/project/{project_id}/aggregated-issues", body=snyk_issues_filter).json()

    return aggregated_issues

def get_snyk_ready_projects_with_issues(snyk_client:SuperSnykClient, snyk_org, gh_repo_full_name) -> List[ProjectIssues]:
    package_manager_names = ["npm", "yarn", "pip", "maven", "gradle", "sbt", "rubygems", "nuget", "gomodules", "govendor", "dep", "cocopods", "composer"] 
    results = list()

    values = { "includeDescription": True, "filters":  { "types": ["vuln"], "ignored": False }  }

    snyk_targets = snyk_org.targets.all()

    target = [x for x in snyk_targets if x.attributes.displayName == gh_repo_full_name][0]

    projects = snyk_client.v3_client.get_v3_pages(f"/orgs/{snyk_org.id}/projects", {"limit": 100, "targetId": target.id})

    for project in projects:
        if project['attributes']['type'] in package_manager_names:
            #issue_set = snyk_client.v1_client.organizations.get(f"{org_id}").projects.get(project['id']).issueset_aggregated.all()
            aggregated_issues = snyk_client.v1_client.post(f"/org/{snyk_org.id}/project/{project['id']}/aggregated-issues", body=values)

            snyk_browser_url = f"https://app.snyk.io/org/{snyk_org.attributes['slug']}/project/{project['id']}"
            package_name = project['attributes']['name'].split(":")[1]
            results.append(ProjectIssues(
                projectId= project['id'], 
                projectName = project['attributes']['name'], 
                projectBrowseUrl = snyk_browser_url,
                packageName = package_name,
                projectType = project['attributes']['type'],
                issues = aggregated_issues))

    return results

def get_snyk_open_projects_for_repo_target(snyk_client:SuperSnykClient, snyk_org, gh_repo_full_name):
    package_manager_names = ["npm", "yarn", "pip", "maven", "gradle", "sbt", "rubygems", "nuget", "gomodules", "govendor", "dep", "cocopods", "composer"]

    #print(f"{gh_repo_full_name=}")
    filter_for_snyk_projects = {  
        "filters": {
           "name": f"{gh_repo_full_name}:",
           "origin": "github"
        }
    }
    snyk_client.v1_client.post(f"/org/{snyk_org.id}/projects", filter_for_snyk_projects)
    projects:List[Project] = snyk_client.v1_client.post(f"/org/{snyk_org.id}/projects", filter_for_snyk_projects).json()

    projects = [x for x in projects['projects'] if x['type'] in package_manager_names]

    return projects

def is_snyk_project_fresh(last_tested_date: str):

    current_time = datetime.utcnow()

    last_tested = datetime.strptime(last_tested_date, '%Y-%m-%dT%H:%M:%S.%fZ')
    total_time = (current_time - last_tested).total_seconds()
    #print(f"seconds since last_tested: {total_time=}")

    if total_time < 180:
        return True
    else:
        return False

def get_manifest_file_path_from_snyk_project_name(name: str):
    name = name.split(':')
    if len(name) == 2:
        return name[1]
    return None
