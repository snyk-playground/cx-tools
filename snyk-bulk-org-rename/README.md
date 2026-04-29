# Snyk bulk organization rename

Command-line tool to rename multiple [Snyk](https://snyk.io/) organizations via the REST API (`PATCH /rest/orgs/{org_id}?version=2024-10-15`).

---

## Requirements

| Requirement | Notes |
|-------------|--------|
| Python | 3.10 or newer recommended |
| Dependencies | [`requests`](https://pypi.org/project/requests/) only (see `requirements.txt`) |
| Access | API token able to manage organizations |

---

## Installation

```bash
cd snyk-bulk-org-rename
pip install -r requirements.txt
```

Set your token (required for every run):

```bash
export SNYK_TOKEN="your-api-token"
```

The tool reads the token **only** from the **`SNYK_TOKEN`** environment variable.

**Optional environment variables**

| Variable | Purpose |
|----------|---------|
| `SNYK_API_URL` | API base URL (default `https://api.snyk.io`). Must be HTTPS under `*.snyk.io` (e.g. `https://api.eu.snyk.io`). Same as `--base-url`. |
| `SNYK_GROUP_ID` | Group UUID for filtering org lists (same as `--group-id`). |

---

## Recommended workflow

Most teams should use **export → edit → apply**: you get a real CSV from Snyk, edit it offline, then apply changes.

### Step 1 — Export a template

Creates **`org_id,new_name`** with **`new_name` prefilled** to each org’s **current** display name.

```bash
python snyk_bulk_org_rename.py --mode export --file orgs-template.csv
```

If your token sees many groups and you only want **one group**, add the **group UUID**:

```bash
python snyk_bulk_org_rename.py --mode export --file orgs-template.csv --group-id "<group-uuid>"
# Or: export SNYK_GROUP_ID="<group-uuid>"   then run export without --group-id
```

### Step 2 — Edit the CSV

Change **`new_name`** only for orgs that should be renamed. Leave other rows as-is (same name as today); those rows are **skipped** when you apply—no API rename call.

### Step 3 — Apply renames

```bash
python snyk_bulk_org_rename.py --mode csv --file orgs-template.csv
```

Optional: **`--dry-run`** prints what would change without calling the API.

---


## Other ways to run

| Situation | What to use |
|-----------|-------------|
| You **already have** a CSV of `org_id` + desired `new_name` | `--mode csv --file your.csv` (skip export). |
| You want everything to happen in one flow from Snyk’s live org list (terminal + optional mapping/pattern) | **`--mode pull`** — see [Pull mode](#pull-mode) below. |

**Quick comparison**

| Mode | Where the list of orgs comes from |
|------|-----------------------------------|
| **`csv`** | **Your CSV file** — only those IDs are processed. |
| **`export`** | **Snyk API** (`GET /rest/orgs`), then writes a file for you to edit elsewhere. |
| **`pull`** | **Snyk API** (`GET /rest/orgs`), then renames in the same run using mapping, pattern, or prompts. |

---

## Pull mode

**Pull mode** is for when you want to **fetch the current org list from Snyk**, see it in the terminal, and **rename in one session**—without using export → edit CSV → csv apply.

### What happens step by step

1. **List orgs** — Calls **`GET /rest/orgs`** (with pagination via **`links.next`**). Optional **`--group-id`** / **`SNYK_GROUP_ID`** limits results to one group.
2. **Print** — Writes each org’s **UUID** and **current name** to the terminal so you can verify what will be touched.
3. **Choose how new names are set** — You pick one of:
   - **`--mapping path/to.csv`** — A CSV of **`org_id`** + **`new_name`** (or **`id`** + **`name`**). Only rows whose **`org_id`** appears both **in this file** and **in the fetched list** are renamed. Any fetched org **missing from the file** is skipped (logged as not in mapping).
   - **`--pattern '...'`** — One template **for every fetched org**. Placeholders: **`{name}`** = current display name, **`{id}`** = org UUID. Example: `Team-{name}`. If the result equals the current name, that org is skipped.
   - **Interactive** (no **`--mapping`** / **`--pattern`**, and a TTY) — You are prompted to enter **either** a mapping file path **or** a pattern string (same rules as above).
4. **Rename** — For each org that needs a new name, sends **PATCH** to update the name (unless **`--dry-run`**, which still runs **GET** to list orgs but does not **PATCH**).

### When to use pull vs export + csv

- **Export + csv** — Better for **reviewing and editing a file** (diffs, approvals, sharing the CSV, or large batch edits in a spreadsheet).
- **Pull** — Better when you already know the mapping or pattern, want a **quick scripted run**, or are fine working **in the terminal** with the live list.

### Pull examples

```bash
# Interactive: list orgs, then prompt for mapping file path or pattern
python snyk_bulk_org_rename.py --mode pull

# Non-interactive: mapping CSV (orgs not in the file are skipped)
python snyk_bulk_org_rename.py --mode pull --mapping ./mapping.csv

# Same pattern for every fetched org: {name} = current name, {id} = UUID
python snyk_bulk_org_rename.py --mode pull --pattern 'PREFIX-{name}'

# Limit listing to one group (combine with mapping or pattern)
python snyk_bulk_org_rename.py --mode pull --group-id "<group-uuid>" --mapping ./mapping.csv
```

Non-interactive **`pull`** (e.g. in CI) requires **`--mapping`** or **`--pattern`**. If both **`--mapping`** and **`--pattern`** are set, **`--mapping`** wins.

---

## CSV format

Files are UTF-8 CSV (Unix or Windows line endings).

### Columns

| Column | Meaning |
|--------|---------|
| **`org_id`** | Organization **UUID** from Snyk (same as `id` in **`GET /rest/orgs`**, org settings, or URLs). **Not** the org slug or free-text name. |
| **`new_name`** | Target display name after rename. |

Headers **`org_id`** and **`new_name`** are required for **`csv`** mode (matching is case-insensitive).  

For **`pull --mapping`** only, you may use **`id`** + **`name`** instead of **`org_id`** + **`new_name`**.

### Examples

```csv
org_id,new_name
aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee,Alpha Team
ffffffff-1111-2222-3333-444444444444,Beta Team
```

Single org (one data row):

```csv
org_id,new_name
aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee,New Org Name
```

Comma inside a name (quoted field):

```csv
org_id,new_name
aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee,"ACME, Inc. - Security"
```

Rows with empty **`org_id`** or **`new_name`** are skipped with a warning.

---

## Group filter (`export` and `pull` only)

To limit **which orgs are listed** from the API to a single group, pass:

```bash
--group-id "<group-uuid>"
```

or set **`SNYK_GROUP_ID`**.

This maps to the REST query parameter **`group_id`** on **`GET /rest/orgs`**.  

**`csv`** mode does **not** use a group filter—your CSV already lists which org IDs to touch.

---

## Logs

For **`csv`** and **`pull`**, each run writes **`rename_log.csv`** by default (override with **`--log-file`**). Columns:

`org_id`, `old_name`, `new_name`, `status`, `error_message`

**`export`** does not produce this log—it only writes the template path you pass to **`--file`**.

---

## Dry run

| Mode | Behavior |
|------|----------|
| **`csv`** | Prints planned renames. **No HTTP requests.** |
| **`export`** | Fetches orgs, prints what would be written. **Does not write** `--file`. |
| **`pull`** | Fetches org list; **PATCH** (rename) calls are **not** sent. |

Add **`--dry-run`**.

---

## Command-line reference

```bash
python snyk_bulk_org_rename.py --mode <csv|export|pull> [options]
```

| Option | Description |
|--------|-------------|
| `--mode csv` | Apply renames from **`--file`**. |
| `--mode export` | Write template to **`--file`** (requires **`--file`**). |
| `--mode pull` | List orgs from API, then rename via mapping/pattern or prompts. |
| `--file PATH` | **csv**: input CSV. **export**: output template path. **Required** for `csv` and `export`. |
| `--group-id UUID` | Limit **`GET /rest/orgs`** to one group (`export` / `pull` only). Also **`SNYK_GROUP_ID`**. |
| `--mapping PATH` | **`pull`**: CSV mapping (`pull` non-interactive). If both **`--mapping`** and **`--pattern`** are set, **mapping wins**. |
| `--pattern 'TEXT'` | **`pull`**: Template with **`{name}`** (current name) and **`{id}`** (org UUID). Applied to every fetched org. |
| `--dry-run` | See [Dry run](#dry-run). |
| `--log-file PATH` | Output log for **`csv`** / **`pull`** (default `rename_log.csv`). |
| `--base-url URL` | HTTPS `*.snyk.io` API base (default from **`SNYK_API_URL`** or `https://api.snyk.io`). |
| `--rate-limit-attempts N` | Max consecutive **HTTP 429** handling rounds per request (default **8**). Uses **`Retry-After`** when present. |
| `-v`, `--verbose` | Debug logging (HTTP traces). |

---

## Rate limits and retries

- **HTTP 429**: Retries with **`Retry-After`** when the server sends it (seconds or HTTP-date). If missing or invalid, waits default to **60 seconds**. Stops after **`--rate-limit-attempts`** (default **8**). Aligned with common Snyk scripting patterns (see e.g. [deactivate-reactivate-all-projects](https://github.com/sam1el/deactivate-reactivate-all-projects)).
- **HTTP 5xx**: Retries with exponential backoff (up to **5** attempts per logical request).

---

## Exit codes

| Code | Meaning |
|------|---------|
| **0** | Finished. Per-org failures appear in the summary and log, not necessarily as process failure. |
| **2** | Missing token, invalid arguments, or non-interactive **`pull`** without **`--mapping`** / **`--pattern`**. |
| **130** | Interrupted (Ctrl+C). |

---

## Security

- Treat **`SNYK_TOKEN`** as a secret; do not commit it or embed it in scripts checked into source control.
- Prefer tokens with the minimum scope needed to rename orgs.
