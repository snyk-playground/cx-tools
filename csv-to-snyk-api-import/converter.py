"""
Pure transformation logic: URL parsing, CSV reading/validation, and
import-projects.json assembly.  No network calls live here.
"""

import csv
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_BRANCH = "main"

# Mapping of hostname patterns to Snyk integration type strings.
# Order matters – first match wins.
HOST_TO_INTEGRATION_TYPE = {
    "github.com": "github",
    "dev.azure.com": "azure-repos",
    "bitbucket.org": "bitbucket-cloud",
}

# All integration types the tool knows how to build targets for.
KNOWN_INTEGRATION_TYPES = (
    "github",
    "github-enterprise",
    "azure-repos",
    "bitbucket-cloud",
    "bitbucket-server",
    "gitlab",
)


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


def detect_integration_type(repo_url: str) -> str | None:
    """Return the Snyk integration type string for a given repo URL.

    Supports github.com, dev.azure.com, and bitbucket.org.
    Returns ``None`` for unrecognised hostnames so the caller can
    prompt the user interactively.

    Raises ValueError for URLs that cannot be parsed.
    """
    parsed = urlparse(repo_url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"Cannot parse hostname from URL: {repo_url}")

    for pattern, integration_type in HOST_TO_INTEGRATION_TYPE.items():
        if hostname == pattern or hostname.endswith(f".{pattern}"):
            return integration_type

    return None


def hostname_from_url(repo_url: str) -> str:
    """Extract the hostname from a URL. Raises ValueError if missing."""
    hostname = urlparse(repo_url).hostname
    if not hostname:
        raise ValueError(f"Cannot parse hostname from URL: {repo_url}")
    return hostname


def parse_repo_url(repo_url: str, integration_type: str | None = None) -> dict:
    """Parse a repo URL into a snyk-api-import ``target`` dict.

    The returned dict shape depends on the integration type:

    GitHub / GitHub Enterprise / Bitbucket Cloud:
        {"owner": ..., "name": ...}

    Azure DevOps:
        {"owner": "<org>/<project>", "name": "<repo>"}

    Bitbucket Server:
        {"repoSlug": ..., "projectKey": ...}

    GitLab:
        {"owner": ..., "name": ...}  (same shape as GitHub)
    """
    parsed = urlparse(repo_url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"Cannot parse hostname from URL: {repo_url}")

    path_parts = [p for p in parsed.path.strip("/").split("/") if p]

    if integration_type is None:
        integration_type = detect_integration_type(repo_url)

    if integration_type == "azure-repos":
        return _parse_azure_url(repo_url, path_parts)

    if integration_type == "bitbucket-server":
        return _parse_bitbucket_server_url(repo_url, path_parts)

    # GitHub, GitHub Enterprise, Bitbucket Cloud, GitLab all use owner/name.
    if len(path_parts) < 2:
        raise ValueError(
            f"URL must follow the pattern "
            f"https://<host>/<owner>/<repo>: {repo_url}"
        )
    name = path_parts[1]
    # Strip .git suffix common in clone URLs
    if name.endswith(".git"):
        name = name[:-4]
    return {
        "owner": path_parts[0],
        "name": name,
    }


def _parse_azure_url(repo_url: str, path_parts: list[str]) -> dict:
    """Parse an Azure DevOps URL: /<org>/<project>/_git/<repo>"""
    if len(path_parts) < 4 or path_parts[2].lower() != "_git":
        raise ValueError(
            f"Azure DevOps URL must follow the pattern "
            f"https://dev.azure.com/<org>/<project>/_git/<repo>: {repo_url}"
        )
    return {
        "owner": f"{path_parts[0]}/{path_parts[1]}",
        "name": path_parts[3],
    }


def _parse_bitbucket_server_url(repo_url: str, path_parts: list[str]) -> dict:
    """Parse a Bitbucket Server URL.

    Supports two common patterns:
        /scm/<projectKey>/<repo>.git
        /projects/<projectKey>/repos/<repo>
    """
    # Clone URL style: /scm/PROJECT/repo.git
    if len(path_parts) >= 3 and path_parts[0].lower() == "scm":
        name = path_parts[2]
        if name.endswith(".git"):
            name = name[:-4]
        return {
            "repoSlug": name,
            "projectKey": path_parts[1],
        }

    # Browse URL style: /projects/PROJECT/repos/repo
    if (
        len(path_parts) >= 4
        and path_parts[0].lower() == "projects"
        and path_parts[2].lower() == "repos"
    ):
        return {
            "repoSlug": path_parts[3],
            "projectKey": path_parts[1],
        }

    raise ValueError(
        f"Bitbucket Server URL must follow one of these patterns:\n"
        f"  https://<host>/scm/<projectKey>/<repo>.git\n"
        f"  https://<host>/projects/<projectKey>/repos/<repo>\n"
        f"Got: {repo_url}"
    )


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------


def read_csv(csv_path: str) -> list[dict]:
    """Read the CSV file and return a list of row dicts."""
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    if not rows:
        raise ValueError(f"CSV file is empty: {csv_path}")
    return rows


def validate_row(row: dict, index: int) -> None:
    """Validate a single CSV row. Raises ValueError on problems."""
    repo_url = (row.get("repo_url") or "").strip()
    if not repo_url:
        raise ValueError(f"Row {index}: 'repo_url' is required")

    org_id = (row.get("snyk_org_id") or "").strip()
    org_name = (row.get("snyk_org_name") or "").strip()
    if not org_id and not org_name:
        raise ValueError(
            f"Row {index}: at least one of 'snyk_org_id' or 'snyk_org_name' is required"
        )


def validate_rows(rows: list[dict]) -> None:
    """Validate all rows; raises on the first error."""
    for i, row in enumerate(rows, start=1):
        validate_row(row, i)


# ---------------------------------------------------------------------------
# Target building
# ---------------------------------------------------------------------------


def _org_id_for_row(row: dict, name_to_org_id: dict[str, str]) -> str:
    org_id = (row.get("snyk_org_id") or "").strip()
    if org_id:
        return org_id
    org_name = (row.get("snyk_org_name") or "").strip()
    return name_to_org_id[org_name]


def build_target(row: dict, integration_type: str | None = None) -> dict:
    """Build a single ``target`` dict from a CSV row."""
    repo_url = row["repo_url"].strip()
    return parse_repo_url(repo_url, integration_type)


def build_import_target(
    row: dict,
    name_to_org_id: dict[str, str],
    integration_cache: dict[tuple[str, str], str],
    host_to_integration: dict[str, str] | None = None,
) -> dict:
    """Build a single import-target entry for the import-projects.json file."""
    repo_url = row["repo_url"].strip()
    org_id = _org_id_for_row(row, name_to_org_id)
    integration_type = resolve_integration_type_for_url(
        repo_url, host_to_integration or {}
    )
    integration_id = integration_cache[(org_id, integration_type)]

    target = build_target(row, integration_type)
    branch = (row.get("branch") or "").strip() or DEFAULT_BRANCH
    target["branch"] = branch

    entry: dict = {
        "orgId": org_id,
        "integrationId": integration_id,
        "target": target,
    }

    exclusion_globs = (row.get("exclusion_globs") or "").strip()
    if exclusion_globs:
        entry["exclusionGlobs"] = exclusion_globs

    return entry


def resolve_integration_type_for_url(
    repo_url: str,
    host_to_integration: dict[str, str],
) -> str:
    """Return the integration type for *repo_url*.

    First tries automatic detection; if that returns ``None`` (unknown host)
    falls back to the user-supplied *host_to_integration* mapping.
    Raises ``KeyError`` if the hostname has not been resolved.
    """
    detected = detect_integration_type(repo_url)
    if detected is not None:
        return detected
    hostname = hostname_from_url(repo_url)
    return host_to_integration[hostname]


def build_import_json(
    rows: list[dict],
    name_to_org_id: dict[str, str],
    integration_cache: dict[tuple[str, str], str],
    host_to_integration: dict[str, str] | None = None,
) -> dict:
    """Build the full import-projects.json structure."""
    h2i = host_to_integration or {}
    targets = [
        build_import_target(row, name_to_org_id, integration_cache, h2i)
        for row in rows
    ]
    return {"targets": targets}
