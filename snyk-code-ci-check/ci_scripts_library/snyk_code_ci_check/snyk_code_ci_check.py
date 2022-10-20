from operator import truediv
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

def test_failed(issue_counts_by_severity):
    num_critsev_issues = issue_counts_by_severity['critical']
    num_highsev_issues = issue_counts_by_severity['high']
    num_medsev_issues  = issue_counts_by_severity['medium']
    num_lowsev_issues  = issue_counts_by_severity['low']

    if num_critsev_issues > 0 or num_highsev_issues > 0:
        return True
    else:
        return False

def get_snyk_code_project_for_repo_target(snyk_client:SuperSnykClient, snyk_org, gh_repo_full_name):

#    print(f"{gh_repo_full_name=}")
    filter_for_snyk_projects = {  
        "filters": {
           "type": "sast",
        }
    }
#    typer.echo(f"org: {snyk_org.id}")
    snyk_client.v1_client.post(f"/org/{snyk_org.id}/projects", filter_for_snyk_projects)
    projects:List[Project] = snyk_client.v1_client.post(f"/org/{snyk_org.id}/projects", filter_for_snyk_projects).json()

    projects = [x for x in projects['projects'] if x['name'] == gh_repo_full_name]

    return projects

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
    )
):
    """
    Check for vulnerable Snyk Code projects for the specified repository
    """
    
    if remote_repo_url is None:
        typer.echo("Remote repo URL not specified. Aborting.")
        raise typer.Exit(code=2)
    else:
        g['repo_full_name'] = get_repo_full_name_from_repo_url(remote_repo_url)

    if snyk_token is None:
        typer.echo("Snyk token not specified. Aborting.")
        raise typer.Exit(code=3)
    else:
        g['snyk_token'] = snyk_token

    if org_slug is None:
        typer.echo("Snyk org not specified. Arborting.")
        raise typer.Exit(code=4)
    else:
        g['snyk_org_slug'] = org_slug
    
    #typer.echo(f"{remote_repo_url=}")
    #typer.echo(f"{g['repo_full_name']=}")

    g['snyk_client'] = SuperSnykClient(g['snyk_token'])
    # typer.echo("Snyk client created successfully")

    typer.echo(f"Checking Snyk Code for projects from {g['repo_full_name']} ...")

    g['snyk_org'] = get_snyk_org_from_slug(g['snyk_client'], g['snyk_org_slug'])

    projects = get_snyk_code_project_for_repo_target(g['snyk_client'], g['snyk_org'], g['repo_full_name'])
    project = projects[0]
    print (project['issueCountsBySeverity'])

    if test_failed(project['issueCountsBySeverity']):
        raise typer.Exit(1)
    
    return

            


if __name__ == "__main__":
    app()