from operator import truediv
import json
import string
import typer
import os
import sys
import time


from lib.super_snyk_client import SuperSnykClient
from lib.snyk_models import Project
from lib.utils import *

# globals
g = {}
g['scriptname'] = "snyk-code-ci-check"
g['retry_delay'] = 180 # 3 minutes
g['retries'] = 3

app = typer.Typer(add_completion=False)


# This function defines the test failure conditions
def test_failed(issue_counts_by_severity):
    num_critsev_issues = issue_counts_by_severity['critical']
    num_highsev_issues = issue_counts_by_severity['high']
    num_medsev_issues  = issue_counts_by_severity['medium']
    num_lowsev_issues  = issue_counts_by_severity['low']

    if num_critsev_issues > 0 or num_highsev_issues > 0:
        return True
    else:
        return False

def log(message: string):
    typer.echo(f"{g['scriptname']}: {message}")

def process_command_line( remote_repo_url: str,
                            remote_repo_branch: str,
                            snyk_token: str,
                            org_slug: str,
                            org_id: str,
                            nofail: bool
                            ):

    config = {}

    if remote_repo_url is None:
        log("Remote repo URL not specified. Aborting.")
        raise typer.Exit(2)
    else:
        config['repo_full_name'] = get_repo_full_name_from_repo_url(remote_repo_url)

    if remote_repo_branch is None:
        log("Branch not specified. Aborting")
        raise typer.Exit(2)
    else:
        config['repo_branch'] = remote_repo_branch

    ## Warn for conflicting options
    if (org_slug and org_id):
        log("warning: both `--org-slug` and `--org-id` specified. `--org-slug` will be ignored.")

    ## Check for Snyk token and initialize the Snyk Client ##
    if snyk_token is None:
        log("Snyk token not specified. Aborting.")
        raise typer.Exit(2)
    else:
        config['snyk_token'] = snyk_token

    try:
        config['snyk_client'] = SuperSnykClient(config['snyk_token'])
        # log("Snyk client created successfully")
    except:
        log("Unable to initialize Snyk client. Aborting.")
        raise type.Exit(3)

    ## Resolve the Snyk org id
    snyk_org = get_snyk_org_id(config['snyk_client'], org_slug, org_id)
    if snyk_org:
        config['snyk_org'] = snyk_org
    else:
        log("Invalid/inaccessible Snyk organization specified. Aborting.")
        raise typer.Exit(2)
    
    config['nofail'] = nofail

    return config


@app.command()
def main(ctx: typer.Context,
    remote_repo_url: str = typer.Option(
        None,
        envvar="REMOTE_REPO_URL",
        help="git url, e.g. https://github.com/owner/repo.git"
    ),
    remote_repo_branch: str = typer.Option(
        None,
        envvar="REMOTE_REPO_BRANCH",
        help="git branch, e.g. main"
    ),
    snyk_token: str = typer.Option(
        None,
        envvar="SNYK_TOKEN",
        help="Please specify your Snyk token. See https://docs.snyk.io/snyk-cli/authenticate-the-cli-with-your-account for how to get your API token, or use a service account: https://docs.snyk.io/features/user-and-group-management/structure-account-for-high-application-performance/service-accounts"
    ),
    org_slug: str = typer.Option(
        None,
        envvar="SNYK_ORG_SLUG",
        help="URL slug for Snyk organization to lookup project"
    ),
    org_id: str = typer.Option(
        None,
        envvar="SNYK_ORG_ID",
        help="UUID for Snyk organization to lookup project"
    ),
    nofail: bool = typer.Option(
        False,
        envvar="SNYK_CODE_CI_CHECK_NOFAIL",
        help="If set, don't perform the Snyk Check. Only the project output will be saved"
    )
):
    """
    Check for vulnerable Snyk Code projects for the specified repository
    """
    
    global g
    g = g | process_command_line(remote_repo_url, remote_repo_branch, snyk_token, org_slug, org_id, nofail)

    log(f"Checking Snyk Code for projects from {g['repo_full_name']}({g['repo_branch']}) ...")

    has_current_test_results = False
    retries_remaining = g['retries']
    delay = g['retry_delay']
    while (not has_current_test_results and retries_remaining > 0):
        projects = get_snyk_code_project_for_repo_target(g['snyk_client'], g['snyk_org'], g['repo_full_name'], g['repo_branch'])

        if projects is None:
            log(f"Unable to retrieve vulnerability data for the '{g['snyk_org']}' Snyk organization. Aborting")
            raise typer.Exit(5)

        if len(projects) == 0:
            log(f"No vulnerability data found for {g['repo_full_name']}({g['repo_branch']}) in Snyk organization {g['snyk_org']}")
            raise typer.Exit(5)
        else:
            project = projects[0] # At present, by definition there can be only one Code Analysis project per repo

        has_current_test_results = is_snyk_project_fresh(project['lastTestedDate'])

        if (not has_current_test_results):
            log(f"Unable to complete check: Snyk Code test results not current")
            log(f"Sleeping {delay} seconds before retrying ({retries_remaining} retries remaining)")
            time.sleep(delay)
            retries_remaining -= 1

    if (not has_current_test_results):
        log(f"Failing Snyk Check: project last tested {project['lastTestedDate']}")
        raise typer.Exit(5)

    #print (project['issueCountsBySeverity'])

    # Write the issues counts to JSON output
    try:
        json_output_filename = f"/project/snyk_code_ci_check-{project['id']}.json"
        with open(json_output_filename, "w") as jsonout:
                json.dump(project['issueCountsBySeverity'], jsonout, indent=2)
                jsonout.write("\n")
                
        log(f"Vulnerability counts (by severity) saved to {json_output_filename}")
    
    except:
        log(f"Warning: unable to write Snyk vulnerability data to {json_output_filename}")

    # Perform the issue check (unless nofail specified)
    if (not g['nofail']):
        if test_failed(project['issueCountsBySeverity']):
            log(f"Failing Snyk Check: {project['issueCountsBySeverity']['critical']} critical vulnerabilities, {project['issueCountsBySeverity']['high']} high severity vulnerabilities")
            raise typer.Exit(1)
        else:
            log(f"No critical or high severity vulnerabilities found.")
    else:
        log(f"NOFAIL specified. Skipping Snyk Check.")

    # test passed, exit(0)    
    return

            


if __name__ == "__main__":
    app()