from operator import truediv
import string
import typer
import os
import sys
import time

sys.path.append("../../ci_scripts_library")

from ci_scripts_library.core.utils import *

from ci_scripts_library.core.utils import *
from ci_scripts_library.core import SuperSnykClient
from snyk.models import Project

app = typer.Typer(add_completion=False)

# globals
g = {}
g['scriptname'] = "snyk-code-ci-check"

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

    return projects

def log(message: string):
    typer.echo(f"{g['scriptname']}: {message}")

@app.command()
def main(ctx: typer.Context,
    remote_repo_url: str = typer.Option(
        None,
        envvar="REMOTE_REPO_URL",
        help="git url, e.g. https://github.com/owner/repo.git"
    ),
    snyk_token: str = typer.Option(
        None,
        envvar="SNYK_TOKEN",
        help="Please specify your Snyk token. See https://docs.snyk.io/snyk-cli/authenticate-the-cli-with-your-account for how to get your API token, or use a service account: https://docs.snyk.io/features/user-and-group-management/structure-account-for-high-application-performance/service-accounts"
    ),
    org_slug: str = typer.Option(
        None,
        envvar="SNYK_ORG_SLUG",
        help="Snyk organization to search for projects"
    ),
    nofail: bool = typer.Option(
        False,
        help="If set, don't perform the Snyk Check. Only the project output will be saved"
    )
):
    """
    Check for vulnerable Snyk Code projects for the specified repository
    """
    
    if remote_repo_url is None:
        log("Remote repo URL not specified. Aborting.")
        raise typer.Exit(code=2)
    else:
        g['repo_full_name'] = get_repo_full_name_from_repo_url(remote_repo_url)

    if snyk_token is None:
        log("Snyk token not specified. Aborting.")
        raise typer.Exit(code=3)
    else:
        g['snyk_token'] = snyk_token

    if org_slug is None:
        log("Snyk org not specified. Arborting.")
        raise typer.Exit(code=4)
    else:
        g['snyk_org_slug'] = org_slug
    
    g['nofail'] = nofail

    #log(f"{remote_repo_url=}")
    #log(f"{g['repo_full_name']=}")

    try:
        g['snyk_client'] = SuperSnykClient(g['snyk_token'])
        # log("Snyk client created successfully")
    except:
        log("Unable to initialize Snyk client. Aborting.")
        raise type.Exit(5)
    
    log(f"Checking Snyk Code for projects from {g['repo_full_name']} ...")

    g['snyk_org'] = get_snyk_org_from_slug(g['snyk_client'], g['snyk_org_slug'])

    if g['snyk_org'] is not None:
        projects = get_snyk_code_project_for_repo_target(g['snyk_client'], g['snyk_org'], g['repo_full_name'])
        if projects:
            project = projects[0]

            if not is_snyk_project_fresh(project['lastTestedDate']):
                log(f"Failing Snyk Check: project last tested {project['lastTestedDate']}")
                raise typer.Exit(5)

            #print (project['issueCountsBySeverity'])
            try:
                json_output_filename = f"/project/snyk_code_ci_check-{project['id']}.json"
                with open(json_output_filename, "w") as jsonout:
                        json.dump(project['issueCountsBySeverity'], jsonout, indent=2)
            except:
                log(f"Warning: unable to write Snyk vulnerability data to {json_output_filename}")
            if (not g['nofail']):
                if test_failed(project['issueCountsBySeverity']):
                    log(f"Failing Snyk Check: {project['issueCountsBySeverity']['critical']} critical vulnerabilities, {project['issueCountsBySeverity']['high']} high severity vulnerabilities")
                    raise typer.Exit(1)
                else:
                    log(f"No critical or high severity vulnerabilities found.")
            else:
                log(f"nofail specified. Skipping Snyk Check.")
        else:
            log(f"Unable to retrieve vulnerability data for the '{g['snyk_org_slug']}' Snyk organization. Aborting")
    else:
        log(f"Unable to retrieve vulnerability data for the '{g['snyk_org_slug']}' Snyk organization. Aborting")
        raise typer.Exit(5)

    # test passed, exit(0)    
    return

            


if __name__ == "__main__":
    app()