# Detect and import new project/s in repo into a target in Snyk

## User need

Use this script to detect new files in a repo which has an existing target in snyk and import them. In this example we're using Github Enterprise as the SCM.

## Flow and Endpoints

### Flow

 - Get a list of all the projects from a Snyk org.
 - Get a list of the files in that repo from the SCM.
 - Compare the lists and find new (Snyk supported) files.
 - Import those files to snyk and check if the import completed

### Endpoints used

 - [Get all Snyk projects](https://snyk.docs.apiary.io/#reference/projects/all-projects/list-all-projects)
 - [Get all files in a repo in GHE](https://docs.github.com/en/rest/git/trees#get-a-tree) - use the recursive flag to get a flat list
 - [Import files to snyk](https://snyk.docs.apiary.io/#reference/integrations/import-projects/import)
 - [Check import status](https://snyk.docs.apiary.io/#reference/integrations/import-job-details/get-import-job-details)

## Code examples

(Pyhton)
```Python
import requests
import os

ORG_ID = ""
INTEGRATION_ID = ""
REPO_NAME = "goof"
GITHUB_ORG = "github-user"
FULL_REPO = f"{GITHUB_ORG}/{REPO_NAME}"
MAIN_BRANCH = "master"

# possible manifest files
possible_manifest_files = [
    "package.json",
    "Gemfile.lock",
    "pom.xml",
    "build.gradle",
    "build.sbt",
    "requirements.txt",
]  # TODO go? C? C++?

# ONLY Snyk Open Source

# get response from snyk -- what files are currently active?
url = f"https://snyk.io/api/v1/org/{ORG_ID}/projects"
snyk_headers = {
    "Content-Type": "application/json",
    "Authorization": "token ****",
}
projects = requests.get(url, headers=snyk_headers).json()["projects"]
projects_in_snyk = {
    os.path.basename(project["name"]).replace(f"{REPO_NAME}:", "")
    for project in projects
}

# get response from GHE -- what manifest files do we have?
url = f"https://ghe.dev.snyk.io/api/v3/repos/{FULL_REPO}/git/trees/{MAIN_BRANCH}?recursive=1"
gh_headers = {
    "Content-Type": "application/json",
    "Authorization": "token *****",
}
resp = requests.get(url, headers=gh_headers).json()
tree = resp["tree"]

# shallow, if we have multiple new same manifest files (e.g multiple pom.xml) this will not work as we are not taking the full path
manifest_files = {
    file["path"]
    for file in tree
    if os.path.basename(file["path"]) in possible_manifest_files
}

# identify the new files that GHE has but Snyk doesn't
missing_projects = manifest_files - projects_in_snyk

# import missing files to Snyk
for project in missing_projects:
    values = {
        "target": {"owner": GITHUB_ORG, "name": REPO_NAME, "branch": MAIN_BRANCH},
        "files": [{"path": project}],
    }
    url = f"https://snyk.io/api/v1/org/{ORG_ID}/integrations/{INTEGRATION_ID}/import"
    resp = requests.post(url, headers=snyk_headers, json=values).json()
    # use get import job details to make sure it actually worked
```
