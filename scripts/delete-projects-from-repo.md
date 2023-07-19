# How to delete all projects of a repo

## Description:
Deletes all projects that match a certain repoURL


## Instructions
1. Make sure you have [pysnyk](https://github.com/snyk-labs/pysnyk) installed. <br>
2. Set your variables inside the script (org ID, API token, repoURL )
3. call : ./your-script-file 

import snyk
import os 

```
repoUrlToDelete = "repo-url-here"
client = snyk.SnykClient("snyk-token-here")
org = client.organizations.get("org-id-here")

projects = org.projects.all()
for project in projects:
  if project.remoteRepoUrl == repoUrlToDelete:
    print("Deleting project:" + project.name )
    project.delete()
```
