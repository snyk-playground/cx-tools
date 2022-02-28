# How to Save Ignored vulns as .snyk file

## Description
This script gives the possibility to create .snyk policy files for each project on am organisation.

It will get the existing list of ignores and display in the ,snyk policy file format.

This script can be used to migrate projects from the SCM (webhook) integration to CLI/ CI-CD integration without loosing the ignores previously done.

Note: All ignores will be for all dependency paths. If needed to have this per dependency path, needs to improve the script.

Install pysnyk before pip3 instal pysnyk <https://github.com/snyk-labs/pysnyk>

How to run:
```
 pythonn3 Save-ignores-as-policy-.py --orgId=YOUR-ORG
```

#### Script
```
import argparse

from snyk import SnykClient
from utils import get_default_token_path, get_token

def parse_command_line_args():
    parser = argparse.ArgumentParser(description="Snyk API Examples")
    parser.add_argument(
        "--orgId", type=str, help="The Snyk Organisation Id", required=True
    )
    return parser.parse_args()

snyk_token_path = get_default_token_path()
snyk_token = get_token(snyk_token_path)
args = parse_command_line_args()
org_id = args.orgId
show_dependencies = True
show_projects = True
client = SnykClient(snyk_token)
projects = client.organizations.get(org_id).projects.all()

for proj in projects:
    project_id = proj.id
    project_name = proj.name
    #print("    Project: %s " % proj.name)
    ignores = proj.ignores.all()

    if len(ignores) > 0:
        print("Project Name: %s" % project_name)
        print("-------.Snyk File-------------")
        print("# Snyk (<https://snyk.io>) policy file, patches or ignores known vulnerabilities.")
        print("# ignores vulnerabilities until expiry date; change duration by modifying expiry date")
        print("ignore:")
        # issues exist for this project
        #print("Project ID: %s" % project_id)

        for next_issue_id in ignores.keys():
            print("  %s:" % next_issue_id)
            print("    - '*':")
            next_issue_ignores = ignores[next_issue_id]
            for next_ignore in next_issue_ignores:
                for i_key in next_ignore.keys():
                    i_value = next_ignore[i_key]
                    reason = i_value["reason"]
                    expires_date = i_value["expires"]

                    print("        reason: %s " % reason)
                    print("        expires: %s " % expires_date)
        print("patch: {}")
        print("#------------end File----------------")
```
