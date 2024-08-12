import requests
import pandas as pd

# Configuration: Replace these values with your actual Snyk API token and organization details
SNYK_API_TOKEN = 'your_snyk_api_token'
ORG_ID = 'your_org_id'  # Replace with your organization ID
API_VERSION = '2024-06-21'  # Replace with the correct API version

# Headers used for API requests
HEADERS = {
    'Authorization': f'token {SNYK_API_TOKEN}',
    'Content-Type': 'application/json'
}

def get_all_targets(org_id):
    """
    Retrieve all targets for the given organization, handling pagination.
    
    Args:
        org_id (str): The organization ID.
    
    Returns:
        list: A list of all target data dictionaries.
    """
    url = f'https://api.snyk.io/rest/orgs/{org_id}/targets?version={API_VERSION}&exclude_empty=false'
    all_targets = []
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        all_targets.extend(data.get('data', []))
        url = data.get('links', {}).get('next')
        if url:
            # Ensure the version is not added twice
            if "version=" not in url:
                url = f'https://api.snyk.io{url}&version={API_VERSION}'
            else:
                url = f'https://api.snyk.io{url}'
    return all_targets

def get_all_projects(org_id):
    """
    Retrieve all projects for the given organization, handling pagination.
    
    Args:
        org_id (str): The organization ID.
    
    Returns:
        list: A list of all project data dictionaries.
    """
    url = f'https://api.snyk.io/rest/orgs/{org_id}/projects?version={API_VERSION}'
    all_projects = []
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        all_projects.extend(data.get('data', []))
        url = data.get('links', {}).get('next')
        if url:
            # Ensure the version is not added twice
            if "version=" not in url:
                url = f'https://api.snyk.io{url}&version={API_VERSION}'
            else:
                url = f'https://api.snyk.io{url}'
    return all_projects

def delete_target(org_id, target_id):
    """
    Delete a specific target by its ID.
    
    Args:
        org_id (str): The organization ID.
        target_id (str): The target ID to delete.
    
    Returns:
        int: HTTP status code of the deletion request.
    """
    url = f'https://api.snyk.io/rest/orgs/{org_id}/targets/{target_id}?version={API_VERSION}'
    response = requests.delete(url, headers=HEADERS)
    return response.status_code

def main(dry_run=True):
    """
    Main function to identify and delete Snyk targets that have no associated projects.
    Provides a summary of targets to be deleted and those to be retained.
    
    Args:
        dry_run (bool): If True, only simulate deletions without making any changes.
    """
    # Retrieve all targets and projects in the organization
    all_targets = get_all_targets(ORG_ID)
    all_projects = get_all_projects(ORG_ID)
    
    # Extract all target IDs
    all_target_ids = [target['id'] for target in all_targets]
    print("All targets:", all_target_ids)
    
    # Identify target IDs that have associated projects
    target_ids_with_projects = {project['relationships']['target']['data']['id'] for project in all_projects if 'target' in project['relationships']}
    print("Targets with associated projects:", target_ids_with_projects)

    # Lists to keep track of targets to delete and to keep
    targets_to_delete = []
    targets_to_keep = []

    # Determine which targets to delete and which to keep
    for target in all_targets:
        target_id = target['id']
        target_name = target['attributes']['display_name']
        
        if target_id not in target_ids_with_projects:
            # Add to delete list
            targets_to_delete.append({'Target ID': target_id, 'Target Name': target_name})
            if not dry_run:
                target_status = delete_target(ORG_ID, target_id)
                if target_status == 204:
                    print(f"Target {target_id} deleted successfully.")
                else:
                    print(f"Failed to delete target {target_id}. Status code: {target_status}")
        else:
            # Add to keep list
            targets_to_keep.append({'Target ID': target_id, 'Target Name': target_name})

    # Create and print summary tables
    print("\nSummary:")
    delete_df = pd.DataFrame(targets_to_delete)
    keep_df = pd.DataFrame(targets_to_keep)

    if not delete_df.empty:
        print("\nTargets to be deleted:")
        print(delete_df.to_string(index=False))
    else:
        print("\nNo targets to delete.")

    if not keep_df.empty:
        print("\nTargets to be kept:")
        print(keep_df.to_string(index=False))
    else:
        print("\nNo targets to keep.")

    # Print the summary counts
    print(f"\nTotal targets to be deleted: {len(targets_to_delete)}")
    print(f"Total targets to be kept: {len(targets_to_keep)}")

if __name__ == '__main__':
    # Run the main function with dry_run enabled to simulate the deletions
    main(dry_run=True)

