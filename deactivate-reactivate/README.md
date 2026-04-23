# deactivate-reactivate-all-projects

The purpose of this script is to run through Snyk organizations, deactivate every selected project, then activate it again. That cycle helps rebuild webhooks for SCM integrations.

Alternatively, **`--activate-inactive-only`** skips deactivate and **only calls activate** on projects that are already inactive (not monitored) in Snyk—see **Activating only inactive projects** below.

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

4. **Set the API region** if your Snyk organization is not on the default instance. Use `SNYK_ENVIRONMENT` and/or `--environment` so API v1, REST, and the OAuth token endpoint all match your tenant (see the **Region / environment** section below). If you use `snyk config environment` for the CLI, use the same value here.

5. Run `main.py` with the options below.

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

## Region / environment

Snyk hosts data in [regional API endpoints](https://docs.snyk.io/snyk-data-and-governance/regional-hosting-and-data-residency). This script must use the same region as the org you are managing, or you will not see the right organizations and projects (or calls may fail).

**Ways to set the region (pick one or combine; CLI flags override the env var where both apply):**

- **`export SNYK_ENVIRONMENT=...`** before running the script. If unset, the default is **`SNYK-US-01`**.
- **`--environment NAME`** on the command line, for example `python3 main.py --environment SNYK-EU-01 --orgs my-org`.

Each preset below sets the **API v1 base**, **REST API base**, and **OAuth2 token** URL together (aligned with `snyk config environment`):

| Name | Notes |
| --- | --- |
| `SNYK-US-01` | Default when `SNYK_ENVIRONMENT` is not set. |
| `SNYK-US-02` | United States (e.g. `api.us.snyk.io`) |
| `SNYK-EU-01` | Europe |
| `SNYK-AU-01` | Australia |
| `SNYK-GOV-01` | Snyk for Government (FedRAMP); also see the **Snyk for Government** section above. |

**Examples:**

```bash
# EU org — env var
export SNYK_ENVIRONMENT=SNYK-EU-01
python3 main.py --orgs my-org
```

```bash
# US-02 org — flag only
python3 main.py --environment SNYK-US-02 --orgs my-org
```

**Advanced:** Override individual bases without changing the rest of the preset: `--api-url`, `--rest-api-url`, and `--oauth-token-url`, or `SNYK_API_URL`, `SNYK_REST_API_URL`, and `SNYK_OAUTH_TOKEN_URL`. Use the same HTTPS and hostname rules as in the **Snyk for Government** section (including `SNYK_ALLOW_UNVERIFIED_API_URL` for nonstandard hosts).

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

## Activating only inactive projects (`--activate-inactive-only`)

By default the script **deactivates then reactivates** every matching project. With **`--activate-inactive-only`**, it **never** deactivates: it only lists and activates projects whose Snyk API field **`isMonitored`** is **false** (inactive / not monitored in the UI). Already-active projects are left unchanged.

The same **`--origin` / `--origins`** filters apply: only inactive projects whose origin passes the filter are activated.

Examples:

```bash
# Preview which inactive projects would be activated
python3 main.py --orgs my-org --activate-inactive-only --dry-run

# Activate only inactive GitHub projects
python3 main.py --orgs my-org --activate-inactive-only --origin github
```

In `main.py`, inactive projects for an org are resolved by the helper **`inactive_projects_in_org`** (origin filter + `not project.isMonitored`).

## Rate limit retries (`--rate-limit-attempts`)

- **`--rate-limit-attempts N`** — maximum number of **consecutive HTTP 429** responses to retry **per API request** before failing (default: **8**). Waits honor `Retry-After` when present.

Example:

```bash
python3 main.py --orgs my-org --rate-limit-attempts 12
```

## Dry run (`--dry-run`) and verbose (`-v` / `--verbose`)

- **`--dry-run`** — Lists orgs and projects that would be changed; does **not** call deactivate or activate. Without **`--activate-inactive-only`**, that means the full deactivate-then-reactivate cycle. With **`--activate-inactive-only`**, only inactive projects that would be activated are listed. Use to confirm the org, region, and (if any) origin filter before a real run.
- **`-v` / `--verbose`** — Prints the resolved **environment and API base URLs**, every org the token can see (id and slug), and for each project the **project id**, **monitored** flag, and each API **ok** result. Use when a run “succeeds” but you are unsure anything happened, or the Snyk UI is confusing.

**If the script exits cleanly but the UI “doesn’t change”:** a full cycle **deactivates and then reactivates** every selected project, so the **normal end state** is still **active** / monitored in the UI—only the **webhooks / integration** are refreshed, which may not look like a visible status flip. If you see a **warning** that no projects were processed, check **region** (`--environment`), **org** slug or UUID, and **`--origins`** (try omitting the origin filter once). If the script prints that some org names were not found, the token or region may not match that org.

**`RequestsDependencyWarning` (urllib3 / chardet / charset_normalizer):** That message comes from the `requests` library on import. It often appears when **`chardet` 6.x** is installed: `requests` only accepts an older `chardet` (see the `chardet` line in `requirements.txt`). Reinstall with `pip install -U -r requirements.txt` (ideally in a venv) so dependencies match. The script still runs; the warning is from `requests` / your environment, not this repo’s code.

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