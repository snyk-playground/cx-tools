# csv-to-snyk-api-import

Converts a CSV of repositories into an `import-projects.json` file for the [snyk-api-import](https://github.com/snyk/snyk-api-import) CLI tool.

## Features

- **Auto-detects integration type** from repo URL (`github.com` → `github`, `dev.azure.com` → `azure-repos`, `bitbucket.org` → `bitbucket-cloud`).
- **Interactive prompt for unknown hosts** — self-hosted instances (GitHub Enterprise, Bitbucket Server, GitLab, etc.) trigger a prompt asking you to select the correct integration type.
- **Resolves or creates Snyk organisations** — provide an existing `snyk_org_id` or a `snyk_org_name` and the script will find-or-create the org from a template.
- **Looks up integration IDs** automatically via the Snyk v1 API.
- **Generates `import-projects.json`** in the exact format snyk-api-import expects.
- **Prompts to run the import** after generating the file.

## Prerequisites

- Python 3.10+
- [snyk-api-import](https://github.com/snyk/snyk-api-import/releases) CLI (on your `PATH` if you want to run imports directly)

## Installation

```bash
pip3 install -r requirements.txt
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SNYK_TOKEN` | **yes** | Your Snyk API token |
| `SNYK_GROUP_ID` | **yes** | Snyk group ID (needed for org creation) |
| `SNYK_TEMPLATE_ORG_ID` | no | Template org ID to clone settings from when creating new orgs |
| `SNYK_LOG_PATH` | no | Log directory for snyk-api-import (defaults to `./logs`) |
| `SNYK_API` | no | Snyk API base URL (defaults to `https://api.snyk.io`) |

## CSV Format

| Column | Required | Description |
|---|---|---|
| `repo_url` | **yes** | Full repository URL |
| `snyk_org_id` | one of these | Existing Snyk org public ID |
| `snyk_org_name` | one of these | Org name — will be found or created |
| `branch` | no | Branch to scan (defaults to `main`) |
| `exclusion_globs` | no | Comma-separated folder names to exclude |

Either `snyk_org_id` or `snyk_org_name` must be provided per row (both is also fine).

See [`sample.csv`](sample.csv) for an example.

## Usage

```bash
# Generate import-projects.json from your CSV
python3 csv_to_snyk_import.py input.csv

# Specify a custom output filename
python3 csv_to_snyk_import.py input.csv my-import.json
```

The script will:

1. Read and validate the CSV.
2. Prompt for the integration type of any unrecognised hostnames (e.g. self-hosted Bitbucket Server, GitLab, GitHub Enterprise).
3. Resolve or create Snyk organisations as needed.
4. Look up integration IDs for each org.
5. Write `import-projects.json`.
6. Ask if you want to run `snyk-api-import` immediately.

### Supported SCM Platforms

| Platform | Auto-detected | Integration type |
|---|---|---|
| GitHub.com | yes | `github` |
| Azure DevOps | yes | `azure-repos` |
| Bitbucket Cloud | yes | `bitbucket-cloud` |
| GitHub Enterprise | prompted | `github-enterprise` |
| Bitbucket Server / Data Center | prompted | `bitbucket-server` |
| GitLab | prompted | `gitlab` |

## Running Tests

```bash
pytest -v test_converter.py
```

All API calls are mocked — tests run entirely offline.

## Generated JSON Format

The output follows the [snyk-api-import format](https://github.com/snyk/snyk-api-import/blob/master/docs/import.md):

```json
{
  "targets": [
    {
      "orgId": "org-abc-123",
      "integrationId": "int-xyz-789",
      "target": {
        "owner": "my-org",
        "name": "my-repo",
        "branch": "main"
      },
      "exclusionGlobs": "fixtures, tests"
    }
  ]
}
```
