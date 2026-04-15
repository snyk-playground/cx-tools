# deactivate-reactivate-all-projects

The purpose of this script is to run through Snyk organizations, deactivate every selected project, then activate it again. That cycle helps rebuild webhooks for SCM integrations.

The script uses the Snyk API with **retry behavior for rate limits**: HTTP **429** responses are retried using the **`Retry-After`** header (seconds or HTTP-date), and transient **5xx** responses use exponential backoff via the `pysnyk` client.

# Requirements

- Python 3.9+ recommended
- Dependencies in `requirements.txt` (`pysnyk`, `yaspin`, and their transitive packages)

# Usage

1. Clone this repository locally.

2. (Optional) Set your Snyk API token. You can find it in your [General Account Settings](https://app.snyk.io/account) after you sign in to Snyk.

   ```bash
   export SNYK_TOKEN={API_TOKEN}
   ```

   If `SNYK_TOKEN` is not set, the script prompts for the token interactively.

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run `main.py` with the options below.

## Selecting organizations (`--orgs`)

- Pass one or more **organization slugs** and/or **organization IDs** (UUID from the Snyk UI or API). Slug matching is **case-insensitive**; the ID must match exactly.
- Omit `--orgs` to be prompted for orgs at runtime.

Examples:

```bash
python3 main.py --orgs my-org-slug
python3 main.py --orgs org-one org-two
python3 main.py --orgs 70158a6b-3a6d-4bff-aace-9699582f5950
```

## Filtering by project origin (`--origin` / `--origins`)

**Either form works**—pick one style, or mix them. Both apply the same filter (and are merged if you use both).

Snyk stores an **`origin`** on each project (SCM / import source, for example `github`, `gitlab`). By default the script processes **all** projects in the chosen orgs.

To limit work to specific origins:

- **`--origin ORIGIN`** — pass once per value (repeat the flag): `--origin github --origin gitlab`.
- **`--origins ORIGIN [ORIGIN ...]`** — pass several values in one go: `--origins github gitlab` (same effect as two `--origin` flags).

Matching is **case-insensitive**. If you do not pass `--origin` or `--origins`, every project origin is included.

Examples:

```bash
# Only GitHub.com projects
python3 main.py --orgs my-org --origin github

# GitHub.com and GitHub Enterprise
python3 main.py --orgs my-org --origin github --origin github-enterprise

# Equivalent using --origins
python3 main.py --orgs my-org --origins github github-enterprise

# Only GitLab
python3 main.py --orgs my-org --origin gitlab
```

Common `origin` values include `github`, `github-enterprise`, `gitlab`, `bitbucket-cloud`, and `azure-repos` (exact strings depend on how projects were imported in Snyk).

## Rate limit retries (`--rate-limit-attempts`)

- **`--rate-limit-attempts N`** — maximum number of **consecutive HTTP 429** responses to retry **per API request** before failing (default: **8**). Waits honor `Retry-After` when present.

Example:

```bash
python3 main.py --orgs my-org --rate-limit-attempts 12
```

# Full example

```bash
export SNYK_TOKEN="your-api-token"
pip install -r requirements.txt
python3 main.py \
  --orgs my-org-slug \
  --origin github --origin github-enterprise \
  --rate-limit-attempts 8
```

Same run using the other flag: `python3 main.py --orgs my-org-slug --origins github github-enterprise --rate-limit-attempts 8`.
