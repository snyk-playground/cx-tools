import requests
import json
import argparse


def deactivate_or_activate_project(org_id, project_id, action, token):
    """
    Deactivates or activates a project based on the specified action.
    """
    url = f"https://api.snyk.io/v1/org/{org_id}/project/{project_id}/{action}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"token {token}",
        "Content-Type": "application/vnd.api+json"
    }

    response = requests.post(url, headers=headers)
    response.raise_for_status()  # Raise exception for non-2xx status codes

    print(f"Project {project_id} successfully {action}d.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deactivate or activate Snyk projects based on a JSON file")
    parser.add_argument("input_file", help="The JSON file containing project information")
    parser.add_argument("--action", choices=["activate", "deactivate"], required=True,
                        help="The action to perform (activate or deactivate)")
    parser.add_argument("--token", required=True, help="Your Snyk API token")
    args = parser.parse_args()

    with open(args.input_file, "r") as f:
        data = json.load(f)

    for project in data:
        org_id = project["org_id"]
        project_id = project["project_id"]
        deactivate_or_activate_project(org_id, project_id, args.action, args.token)

    print("All projects successfully {action}d.".format(action=args.action))
