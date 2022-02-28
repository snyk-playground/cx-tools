# How to Copy ignore from one project to another

## Description:
This script retrieves the ignores from one project, and add it to another.

This script can be used to migrate projects from the SCM (webhook) integration to CLI/ CI-CD integration without loosing the ignores previously done.

Note: All ignores will be for all dependency paths. This script is not checking if the ignore already exist on the target project, if it exists it will be added in addition (resulting on 2 ignores)

Note: Needs to install pysnyk before: [<https://github.com/snyk-labs/pysnyk>](<https://github.com/snyk-labs/pysnyk>)

### Script / Code Example

```
python3 your-file-name.py --orgId=YOUR-ORG --inProj=SOURCE-PROJECT --outProj=TARGET-PROJECT

import argparse

from snyk import SnykClient
from utils import get_default_token_path, get_token

def parse_command_line_args():
    parser = argparse.ArgumentParser(description="Snyk API Examples")
    parser.add_argument(
        "--orgId", type=str, help="The Snyk Organisation Id", required=True
    )
    parser.add_argument(
        "--inProj", type=str, help="The ID for the input project", required=True
    )
    parser.add_argument(
        "--outProj", type=str, help="The ID for the output project", required=True
    )

    return parser.parse_args()

snyk_token_path = get_default_token_path()
snyk_token = get_token(snyk_token_path)
args = parse_command_line_args()
org_id = args.orgId
project_id = args.inProj
outProj = args.outProj

show_dependencies = True
show_projects = True
client = SnykClient(snyk_token)
ignores = client.organizations.get(org_id).projects.get(project_id).ignores.all()

if len(ignores) > 0:
    #print("Project Name: %s" % project_name)
    print("-------start-------------")

    for issueID in ignores.keys():
        print("  Vuln ID %s " % issueID)
        next_issue_ignores = ignores[issueID]

        for next_ignore in next_issue_ignores:
            for i_key in next_ignore.keys():
                i_value = next_ignore[i_key]
                values_object = {
                    "ignorePath": "",
                    "reasonType": i_value["reasonType"],
                    "disregardIfFixable": False,
                    "reason" : i_value["reason"],
                    "expires" : i_value["expires"]
                    }

        api_url = "org/" + org_id + "/project/" + outProj + "/ignore/" + issueID
        print("  %s" % api_url)
        r2 = client.post(api_url, values_object)

    #print("patch: {}")
    print("#------------end ----------------")
```
