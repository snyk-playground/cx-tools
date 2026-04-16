# deactivate-reactivate-all-projects

The purpose of this script is to run through Snyk organizations, deactivate every selected project, then activate it again. That cycle helps rebuild webhooks for SCM integrations.

The script uses the Snyk API with **retry behavior for rate limits**: HTTP **429** responses are retried using the **`Retry-After`** header (seconds or HTTP-date), and transient **5xx** responses use exponential backoff via the `pysnyk` client.

# Requirements

- Python 3.9+ recommended
- Dependencies in `requirements.txt` (`pysnyk`, `yaspin`, and their transitive packages)

# Usage

1. Clone this repository locally.

2. **Authenticate.** The script picks credentials in this order (first match wins):

   | Priority | Variables | Notes |
   | --- | --- | --- |
   | 1 | `SNYK_OAUTH_CLIENT_ID` and `SNYK_OAUTH_CLIENT_SECRET` | OAuth 2.0 **client credentials** (recommended for automation). Short-lived access tokens are obtained from the OAuth token endpoint and refreshed automatically before expiry. |
   | 2 | `SNYK_OAUTH_TOKEN` | A short-lived OAuth **access token** (same usage as the Snyk CLI). You must refresh it yourself when it expires; use client credentials instead if you need long runs. |
   | 3 | `SNYK_TOKEN` | Classic API token (`Authorization: token …`). **Not available in Snyk for Government (FedRAMP)**; see below. |

   If none of these are set and you are **not** targeting Gov, the script prompts for `SNYK_TOKEN` interactively.

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run `main.py` with the options below.

## Snyk for Government (FedRAMP / `SNYK-GOV-01`)

[Snyk for Government (US)](https://docs.snyk.io/snyk-data-and-governance/snyk-for-government-us) does **not** allow static API tokens. You must use **OAuth 2.0**—typically a service account with the **client credentials** grant. Access tokens are used like API keys but with `Authorization: Bearer` semantics and a short TTL; this script refreshes them when you use `SNYK_OAUTH_CLIENT_ID` / `SNYK_OAUTH_CLIENT_SECRET`.

1. Create an OAuth 2.0 service account (UI or API) and store **client ID** and **client secret** securely.
2. Point the script at the Gov API endpoints using **`--environment SNYK-GOV-01`** (or `export SNYK_ENVIRONMENT=SNYK-GOV-01`). That selects `https://api.snykgov.io` for API v1, REST, and `/oauth2/token`, consistent with [regional URL documentation](https://docs.snyk.io/snyk-data-and-governance/regional-hosting-and-data-residency).
3. Export credentials and run:

```bash
export SNYK_ENVIRONMENT=SNYK-GOV-01
export SNYK_OAUTH_CLIENT_ID="your-client-id"
export SNYK_OAUTH_CLIENT_SECRET="your-client-secret"
pip install -r requirements.txt
python3 main.py --orgs your-org-slug
```

Optional: override URLs with `--api-url`, `--rest-api-url`, or `--oauth-token-url`, or the `SNYK_API_URL`, `SNYK_REST_API_URL`, and `SNYK_OAUTH_TOKEN_URL` environment variables. For security, URLs must use **HTTPS** and hostnames under **`*.snyk.io`** or **`*.snykgov.io`**. If your tenant uses another hostname, set `SNYK_ALLOW_UNVERIFIED_API_URL=1` (HTTPS is still required).

## Region / environment (`--environment`)

Use the same region names as `snyk config environment` (for example `SNYK-US-02`, `SNYK-EU-01`, `SNYK-GOV-01`). This sets default API and OAuth token URLs. You can override individual URLs as needed.

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

# Full examples

**Commercial (API token):**

```bash
export SNYK_TOKEN="your-api-token"
pip install -r requirements.txt
python3 main.py \
  --orgs my-org-slug \
  --origin github --origin github-enterprise \
  --rate-limit-attempts 8
```

Same run using the other flag: `python3 main.py --orgs my-org-slug --origins github github-enterprise --rate-limit-attempts 8`.

**OAuth client credentials (Enterprise / Gov-compatible):**

```bash
export SNYK_OAUTH_CLIENT_ID="…"
export SNYK_OAUTH_CLIENT_SECRET="…"
# For Gov:
# export SNYK_ENVIRONMENT=SNYK-GOV-01
pip install -r requirements.txt
python3 main.py --orgs my-org-slug
```