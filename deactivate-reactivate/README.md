# deactivate-reactivate-all-projects

Cycle Snyk projects **deactivate → activate** so SCM **webhooks** can be rebuilt. You pick one or more organizations; the script walks the projects you care about and calls the Snyk API for each.

**Optional:** **`--activate-inactive-only`** skips deactivate and only **activates** projects that are already inactive (not monitored)—useful when you only want to turn monitoring back on.

**Reliability:** HTTP **429** (rate limit) responses are retried using **`Retry-After`**; transient **5xx** errors use backoff from the underlying `pysnyk` client.

---

## Quick start (most customers)

1. **Clone** this repo and install:

   ```bash
   pip install -r requirements.txt
   ```

2. **Set a token** (same idea as the Snyk CLI—use a token that can manage the target orgs):

   ```bash
   export SNYK_TOKEN="your-snyk-api-token"
   ```

3. **Preview**, then run:

   ```bash
   # See what would change (no API writes)
   python3 main.py --orgs your-org-slug --dry-run

   # Then run for real
   python3 main.py --orgs your-org-slug
   ```

If your Snyk data is **not** on the default US instance, set region first (see **Region** below)—wrong region usually means “wrong orgs or empty project list.”

**Large orgs (many thousands of projects):** add **`--workers 12`** (or 8–16) so deactivate/activate calls run in parallel. Requires `SNYK_TOKEN` (or OAuth env vars) in the environment—not an interactive prompt.

---

## What to pass (cheat sheet)

| You want to… | Use |
| --- | --- |
| Pick org(s) | **`--orgs slug-or-uuid`** (repeat or space-separate multiple). Omit to be prompted. |
| Preview only | **`--dry-run`** |
| Speed up huge runs | **`--workers N`** (try **8–16**; max **64**) |
| Limit to GitHub / GitLab / etc. | **`--origin github`** (repeat) or **`--origins github gitlab`** |
| Only turn on inactive projects | **`--activate-inactive-only`** |
| EU / AU / second US shard | **`--environment SNYK-EU-01`** (etc.) or **`export SNYK_ENVIRONMENT=...`** |
| More 429 retries per request | **`--rate-limit-attempts 12`** (default **8**) |
| Debug API / org visibility | **`-v`** / **`--verbose`** |

Use **`--dry-run`** until the org names, region, and optional origin filter look right.

---

## Authentication

The script uses the **first** of these that is set:

| Order | Environment variables | When to use |
| --- | --- | --- |
| 1 | **`SNYK_OAUTH_CLIENT_ID`** + **`SNYK_OAUTH_CLIENT_SECRET`** | Automation / long runs; tokens refresh automatically. |
| 2 | **`SNYK_OAUTH_TOKEN`** | Short-lived access token (you refresh it yourself). |
| 3 | **`SNYK_TOKEN`** | Classic Snyk API token. |

If nothing is set and you are **not** on Snyk for Government, the script may **prompt** for `SNYK_TOKEN`. **Parallel mode** (`--workers` > 1) **always** needs credentials in the environment (no prompt).

**Snyk for Government (FedRAMP):** static **`SNYK_TOKEN` is not supported**—use OAuth client credentials and **`--environment SNYK-GOV-01`**. Short instructions: **[Snyk for Government](#optional-snyk-for-government-fedramp)** at the end of this file.

---

## Region / environment

Snyk is hosted in [regions](https://docs.snyk.io/snyk-data-and-governance/regional-hosting-and-data-residency). The script must match **your** org’s region or listing will look wrong.

- **Default:** **`SNYK-US-01`** if you set nothing (same idea as `snyk config environment`).
- **Set once:** `export SNYK_ENVIRONMENT=SNYK-EU-01` **or** `python3 main.py --environment SNYK-EU-01 --orgs my-org`.

| `SNYK_ENVIRONMENT` / `--environment` | Typical use |
| --- | --- |
| `SNYK-US-01` | Default US |
| `SNYK-US-02` | US (`api.us.snyk.io`) |
| `SNYK-EU-01` | Europe |
| `SNYK-AU-01` | Australia |
| `SNYK-GOV-01` | US Government / FedRAMP (OAuth only—see appendix) |

**Advanced:** Override URLs with **`--api-url`**, **`--rest-api-url`**, **`--oauth-token-url`** or **`SNYK_API_URL`**, **`SNYK_REST_API_URL`**, **`SNYK_OAUTH_TOKEN_URL`**. URLs must be **HTTPS**; by default hostnames must be under **`*.snyk.io`** or **`*.snykgov.io`**. Other hosts: set **`SNYK_ALLOW_UNVERIFIED_API_URL=1`** (HTTPS still required).

---

## Organizations (`--orgs`)

Pass **slug** and/or **org id (UUID)**. Slug match is case-insensitive; UUID must match exactly.

```bash
python3 main.py --orgs my-org-slug
python3 main.py --orgs org-one org-two
python3 main.py --orgs 70158a6b-3a6d-4bff-aace-9699582f5950
```

---

## Filtering by SCM origin (`--origin` / `--origins`)

By default **all** project origins in the org are processed. To limit to certain import sources, use either style (you can mix them):

- **`--origin github --origin gitlab`**
- **`--origins github gitlab`**

Values are **case-insensitive** and must match what the API returns. Many GitHub App imports show as **`github-cloud-app`**, not `github`—run **`--dry-run`** once and copy the **`Origin:`** line if you are unsure.

```bash
python3 main.py --orgs my-org --origin github-cloud-app
python3 main.py --orgs my-org --origins github gitlab
```

---

## Activate only inactive projects (`--activate-inactive-only`)

Does **not** deactivate. Only **activates** projects that are already inactive (`isMonitored` false). Same **`--origin` / `--origins`** filters apply.

```bash
python3 main.py --orgs my-org --activate-inactive-only --dry-run
python3 main.py --orgs my-org --activate-inactive-only --origin github
```

---

## Parallel workers (`--workers`)

Each project needs **two** API calls for a full cycle (deactivate, then activate). On large tenants that is mostly **waiting on the network**, so **`--workers N`** runs up to **N** of those calls at the same time (default **1** = same as always).

- Try **8–16** first; raise if 429s stay rare, lower if runs stall on rate limits.
- Max **64**.
- **`--workers` > 1:** set **`SNYK_TOKEN`** or OAuth variables in the environment (no interactive token).
- With **N > 1**, spinners are replaced by a one-line note per org.

```bash
export SNYK_TOKEN="your-api-token"
python3 main.py --orgs my-org --workers 12
```

---

## Rate limits (`--rate-limit-attempts`)

Max **consecutive HTTP 429** retries **per request** before failing (default **8**). Waits follow **`Retry-After`** when the API sends it.

```bash
python3 main.py --orgs my-org --rate-limit-attempts 12
```

---

## Dry run and verbose

- **`--dry-run`** — List what would happen; **no** deactivate/activate.
- **`-v` / `--verbose`** — Print API bases, orgs visible to the token, and per-project ids/results.

**UI looks unchanged after a full cycle:** projects end **active** again; the goal is often **webhooks / integration**, not a lasting “off” state. If nothing processed, check **region**, **org slug/UUID**, and try without **`--origin`** once.

**`RequestsDependencyWarning`:** Usually a **`chardet`** version mismatch in your environment. Use **`pip install -U -r requirements.txt`** in a venv; see `requirements.txt` for the pinned range.

---

## Requirements

- Python **3.9+** recommended  
- **`pip install -r requirements.txt`**

---

## Copy-paste examples

**API token, commercial (typical):**

```bash
export SNYK_TOKEN="your-api-token"
pip install -r requirements.txt
python3 main.py --orgs my-org-slug --dry-run
python3 main.py --orgs my-org-slug --workers 12
```

**OAuth client credentials (good for automation):**

```bash
export SNYK_OAUTH_CLIENT_ID="…"
export SNYK_OAUTH_CLIENT_SECRET="…"
pip install -r requirements.txt
python3 main.py --orgs my-org-slug --workers 12
```

---

## Optional: Snyk for Government (FedRAMP)

[Snyk for Government](https://docs.snyk.io/snyk-data-and-governance/snyk-for-government-us) does **not** allow static API tokens. Use **OAuth 2.0** (service account **client credentials**). This script refreshes access tokens when **`SNYK_OAUTH_CLIENT_ID`** and **`SNYK_OAUTH_CLIENT_SECRET`** are set.

```bash
export SNYK_ENVIRONMENT=SNYK-GOV-01
export SNYK_OAUTH_CLIENT_ID="your-client-id"
export SNYK_OAUTH_CLIENT_SECRET="your-client-secret"
pip install -r requirements.txt
python3 main.py --orgs your-org-slug
```

Same **HTTPS / hostname** rules and optional **`SNYK_ALLOW_UNVERIFIED_API_URL=1`** as in **Region / environment** above.
