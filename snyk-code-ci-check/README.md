# snyk-code-ci-check

### Description

This example illustrates how to use the Snyk API to query project test results for Snyk Code, and how to fail a pipeline based on simple conditions from those results.

In this example, the failure conditions are "any critical or high severity vulnerabilities in the project"

Vulnerability data is written to `snyk_code_ci_check-<snyk_project_id>.json` in the directory you mount to `/project` when running the container

### Usage

When running via `docker`:

```
docker run -it --rm -v ${PWD}:/project snyk-code-ci-check:latest --remote-repo-url https://github.com/juice-shop/juice-shop --org snyk-org-slug --snyk-token $SNYK_TOKEN
```

To prevent failing your pipeline, you can add the `--nofail` option:
```
docker run -it --rm -v ${PWD}:/project snyk-code-ci-check:latest --remote-repo-url https://github.com/juice-shop/juice-shop --org snyk-org-slug --snyk-token $SNYK_TOKEN --nofail
```

Alternatively, you may specify options via the following environment variables:

* REMOTE_REPO_URL - the URL of the repository to retrieve Snyk project data for
* SNYK_ORG_SLUG - the org slug of the Snyk organization in which the project data can be found
* SNYK_TOKEN - a valid Snyk API token for the specified Snyk organization
* SNYK_CODE_CI_CHECK_NOFAIL - set to "True" to prevent the check from failing a pipeline

## Bitbucket Pipelines example

```
pipelines:
  default:
    - step:
        name: 'Build'
        script:
          - npm ci
    - step:
        name: 'Snyk Code CI Check'
        image: snyk-code-ci-check:latest
        script:
          - python /app/ci_scripts_library/snyk_code_ci_check/snyk_code_ci_check.py
 ```

### Acknowledgements

This example uses [typer](https://typer.tiangolo.com/) for CLI interactions

This example's dependencies are managed with [Poetry](https://python-poetry.org/).
