import argparse
import os
import sys
import urllib.parse
import requests
from dateutil import parser
from datetime import timezone

# Standard Snyk REST API version
API_VERSION = "2024-10-15"

def parse_date(date_str):
    if not date_str:
        return None
    dt = parser.parse(date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def get_product(project_type):
    """Mapping a Snyk project type to a product category."""
    project_type = project_type.lower()
    if project_type == "sast":
        return "sast"
    if project_type in ["terraformconfig", "k8sconfig", "helmconfig", "cloudformationconfig", "armtemplate", "kubernetes"]:
        return "iac"
    if project_type in ["dockerfile", "apk", "rpm", "deb", "linux"]:
        return "container"
    return "opensource"

class SnykRestClient:
    """HTTP client for the Snyk REST API."""
    def __init__(self, token, region=""):
        self.base_rest_url = self._get_regional_url(region)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        })

    def _get_regional_url(self, region: str) -> str:
        """Determine the correct Snyk REST API base URL based on the region."""
        region = region.lower().strip()
        if not region or region in ["default", "us-01"]:
            return "https://api.snyk.io/rest"
        if region in ["us-02", "us"]:
            return "https://api.us.snyk.io/rest"
        if region in ["eu-01", "eu"]:
            return "https://api.eu.snyk.io/rest"
        if region in ["au-01", "au"]:
            return "https://api.au.snyk.io/rest"
        return f"https://api.{region}.snyk.io/rest"

    def _get_paginated(self, url, params=None):
        if params is None:
            params = {}
        if "version" not in params:
            params["version"] = API_VERSION
        if "limit" not in params:
            params["limit"] = 100

        results = []
        current_url = url

        while current_url:
            resp = self.session.get(current_url, params=params if '?' not in current_url else None)
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"Error fetching data from {current_url}: {e.response.text}", file=sys.stderr)
                sys.exit(1)
            
            data = resp.json()
            results.extend(data.get("data", []))
            
            next_link = data.get("links", {}).get("next")
            if next_link:
                if next_link.startswith("http"):
                    current_url = next_link
                else:
                    parsed_base = urllib.parse.urlparse(self.base_rest_url)
                    current_url = f"{parsed_base.scheme}://{parsed_base.netloc}{next_link}"
                # Set params to None because the 'next' URL from Snyk already has them urlencoded in the string
                params = None 
            else:
                current_url = None
                
        return results

    def get_orgs(self):
        return self._get_paginated(f"{self.base_rest_url}/orgs")

    def get_projects(self, org_id):
        return self._get_paginated(f"{self.base_rest_url}/orgs/{org_id}/projects")

    def get_targets(self, org_id, source_types=None, exclude_empty=False):
        """
        Fetch targets using native REST API spec filters. 
        - exclude_empty=False overrides the API default behavior which would hide 0-project targets.
        """
        params = {}
        if source_types:
            params["source_types"] = ",".join(source_types)
        
        params["exclude_empty"] = "true" if exclude_empty else "false"

        return self._get_paginated(f"{self.base_rest_url}/orgs/{org_id}/targets", params=params)

    def delete_project(self, org_id, project_id):
        url = f"{self.base_rest_url}/orgs/{org_id}/projects/{project_id}?version={API_VERSION}"
        resp = self.session.delete(url)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Failed to delete project {project_id}: {e.response.text}", file=sys.stderr)

    def deactivate_project(self, org_id, project_id):
        url = f"{self.base_rest_url}/orgs/{org_id}/projects/{project_id}?version={API_VERSION}"
        payload = {
            "data": {
                "id": project_id,
                "type": "project",
                "attributes": {
                    "status": "inactive"
                }
            }
        }
        resp = self.session.patch(url, json=payload)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Failed to deactivate project {project_id}: {e.response.text}", file=sys.stderr)

    def delete_target(self, org_id, target_id):
        url = f"{self.base_rest_url}/orgs/{org_id}/targets/{target_id}?version={API_VERSION}"
        resp = self.session.delete(url)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Failed to delete target {target_id}: {e.response.text}", file=sys.stderr)

    def delete_org(self, org_id):
        url = f"{self.base_rest_url}/orgs/{org_id}?version={API_VERSION}"
        resp = self.session.delete(url)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Failed to delete org {org_id}: {e.response.text}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Bulk delete Snyk targets or projects using only the REST API",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=45, width=150))
    parser.add_argument("--orgs", required=True, help="A set of org slugs upon which to perform operations (use ! for all orgs).")
    parser.add_argument("--region", default="", help="Snyk API region (e.g., 'eu', 'au', 'us-02'). Leave empty for default (US-01 global).")
    
    # Shared Filters
    parser.add_argument("--origins", default="", help="Defines origin/source_types of projects/targets to delete (e.g., github, cli).")
    parser.add_argument("--ignore-keys", default="", help="If any of these keys are present in a project/target name, it will not be targeted.")
    
    # Target Mode
    parser.add_argument("--targets", action="store_true", help="[Mode] Query and delete Targets directly instead of Projects.")

    # Project Specific Filters
    parser.add_argument("--sca-types", default="", help="[Project Mode Only] Defines SCA type/s to delete.")
    parser.add_argument("--products", default="", help="[Project Mode Only] Defines product/s types to delete (opensource, container, iac, or sast).")
    parser.add_argument("--after", default=None, help="[Project Mode Only] Delete projects created after date time (ISO 8601).")
    parser.add_argument("--before", default=None, help="[Project Mode Only] Delete projects created before date time (ISO 8601).")
    parser.add_argument("--delete", action="store_true", help="[Project Mode Only] Delete active projects instead of deactivating them.")
    parser.add_argument("--delete-non-active-projects", action="store_true", help="[Project Mode Only] Delete non-active projects instead of deactivating.")
    
    # Global Actions
    parser.add_argument("--delete-empty-orgs", action="store_true", help="Delete all orgs that do not have any remaining projects.")
    parser.add_argument("--force", action="store_true", help="Apply actions (script runs as dry run by default).")
    
    args = parser.parse_args()

    token = os.environ.get("SNYK_TOKEN")
    if not token:
        print("Error: Please set your SNYK_TOKEN environment variable.")
        sys.exit(1)

    client = SnykRestClient(token, args.region)

    target_org_slugs = args.orgs.split() if args.orgs != "!" else []
    sca_types = args.sca_types.split()
    products = args.products.split()
    origins = args.origins.split()
    ignore_keys = args.ignore_keys.split()
    after_dt = parse_date(args.after)
    before_dt = parse_date(args.before)

    print("Fetching organizations...")
    all_orgs = client.get_orgs()

    if args.orgs == "!":
        orgs_to_process = all_orgs
    else:
        orgs_to_process = [o for o in all_orgs if o.get("attributes", {}).get("slug") in target_org_slugs]

    if not orgs_to_process:
        print("No matching organizations found.")
        sys.exit(0)

    for org in orgs_to_process:
        org_id = org["id"]
        org_name = org.get("attributes", {}).get("name")
        org_slug = org.get("attributes", {}).get("slug")

        print(f"\nScanning Org: {org_name} ({org_slug})")

        if args.targets:
            # ========================
            # TARGET MODE
            # ========================
            
            # Use strict API filters based on the spec
            targets = client.get_targets(org_id, source_types=origins, exclude_empty=False)
            targets_to_action = []

            for t in targets:
                attrs = t.get("attributes", {})
                t_name = attrs.get("display_name") or "Unknown Target"

                # Check string exclusion keys
                if ignore_keys and any(key in t_name for key in ignore_keys):
                    continue

                targets_to_action.append(t)

            if not targets_to_action:
                print("  No targets matched criteria.")
            else:
                for t in targets_to_action:
                    t_id = t["id"]
                    t_name = t.get("attributes", {}).get("display_name", "Unknown Target")
                    
                    if args.force:
                        print(f"  [DELETE TARGET] {t_name} ({t_id})")
                        client.delete_target(org_id, t_id)
                    else:
                        print(f"  [DRY RUN - DELETE TARGET] {t_name} ({t_id})")

        else:
            # ========================
            # PROJECT MODE
            # ========================
            projects = client.get_projects(org_id)
            projects_to_action = []

            for p in projects:
                attrs = p.get("attributes", {})
                p_name = attrs.get("name", "")
                p_type = attrs.get("type", "")
                p_origin = attrs.get("origin", "")
                p_status = attrs.get("status", "active")
                p_created = attrs.get("created", "")
                is_active = (p_status == "active")

                if args.delete_non_active_projects and is_active:
                    continue
                if not args.delete_non_active_projects and not is_active:
                    continue

                if ignore_keys and any(key in p_name for key in ignore_keys):
                    continue
                if sca_types and p_type not in sca_types:
                    continue
                if origins and p_origin not in origins:
                    continue
                if products and get_product(p_type) not in products:
                    continue

                created_dt = parse_date(p_created)
                if created_dt:
                    if after_dt and created_dt <= after_dt:
                        continue
                    if before_dt and created_dt >= before_dt:
                        continue

                projects_to_action.append(p)

            if not projects_to_action:
                print("  No projects matched criteria for action.")
            else:
                for p in projects_to_action:
                    p_id = p["id"]
                    p_name = p.get("attributes", {}).get("name")
                    
                    action_is_delete = args.delete or args.delete_non_active_projects
                    action_verb = "DELETE" if action_is_delete else "DEACTIVATE"
                    
                    if args.force:
                        print(f"  [{action_verb}] {p_name} ({p_id})")
                        if action_is_delete:
                            client.delete_project(org_id, p_id)
                        else:
                            client.deactivate_project(org_id, p_id)
                    else:
                        print(f"  [DRY RUN - {action_verb}] {p_name} ({p_id})")

        # ========================
        # ORG CLEANUP CHECK
        # ========================
        if args.delete_empty_orgs:
            rem_projects = client.get_projects(org_id)
            if not rem_projects:
                if args.force:
                    print(f"  [DELETE ORG] {org_name} is empty. Deleting via REST API...")
                    client.delete_org(org_id)
                else:
                    print(f"  [DRY RUN - DELETE ORG] {org_name} is empty.")
            else:
                print(f"  [INFO] {org_name} is not empty ({len(rem_projects)} projects remain).")

if __name__ == "__main__":
    main()