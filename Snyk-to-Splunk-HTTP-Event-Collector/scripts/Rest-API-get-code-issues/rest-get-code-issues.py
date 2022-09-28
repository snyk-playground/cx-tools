import httpx
import json
import logging

"""
run: pip3 install -r requirements.txt

Get results and write them into a .json file:
python3 rest-get-code-issues.py 2>&1 | sed '1,5d;$d' | sed '$d' | tee asd.json

"""

logging.basicConfig(level=logging.DEBUG)


def create_client(base_url: str, token: str) -> httpx.Client:
    """Create a client."""
    client = httpx.Client(
        base_url=base_url,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/vnd.api+json",
            "Authorization": f"Token {token}",
        },
    )
    return client


def get_code_issues(client: httpx.Client, org_id: str, proj_id: str, severity: str) -> httpx.Response:
    """Get code issues for Code."""

    response = client.get(f"/orgs/{org_id}/issues?project_id={proj_id}&severity={severity}&type=code&version=2022-04-06%7Eexperimental")
    return response.json()


def main():
    """Main function."""

    SNYK_TOKEN = "..."  # Snyk personal API Token
    ORG_ID = "..."  # Snyk Org.ID storybooks
    PROJ_ID = "..."  # Snyk storybooks Code Analysis
    SEVERITY = "high"  # severity of the code issues

    client = create_client(base_url="https://api.snyk.io/rest/", token=SNYK_TOKEN)

    it = get_code_issues(client, org_id=ORG_ID, proj_id=PROJ_ID, severity=SEVERITY)
    logging.debug(json.dumps(it, indent=2))


if __name__ == '__main__':
    main()
