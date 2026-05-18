"""
Thin wrappers around the Snyk v1 REST API.
"""

import os

import requests

DEFAULT_API_BASE = "https://api.snyk.io"


def _api_base() -> str:
    base = os.environ.get("SNYK_API", DEFAULT_API_BASE).rstrip("/")
    # Users may set SNYK_API with a trailing /v1 (required by snyk-api-import).
    # Strip it here so our own URL construction doesn't double up to /v1/v1.
    if base.endswith("/v1"):
        base = base[:-3]
    return base


def _auth_header() -> dict:
    token = os.environ.get("SNYK_TOKEN")
    if not token:
        raise EnvironmentError("SNYK_TOKEN environment variable is not set")
    return {"Authorization": f"token {token}"}


def list_orgs() -> list[dict]:
    """Return all Snyk organisations the token has access to."""
    url = f"{_api_base()}/v1/orgs"
    resp = requests.get(url, headers=_auth_header(), timeout=30)
    if not resp.ok:
        detail = resp.text
        try:
            detail = resp.json()
        except Exception:
            pass
        raise RuntimeError(
            f"Failed to list organisations (HTTP {resp.status_code}): {detail}\n"
            f"Check that SNYK_TOKEN is valid and has the correct permissions."
        )
    return resp.json().get("orgs", [])


def create_org(name: str, group_id: str, source_org_id: str | None = None) -> dict:
    """Create a new Snyk organisation, optionally cloned from a template."""
    if not group_id:
        raise ValueError(
            "SNYK_GROUP_ID is required to create organisations. "
            "Set it via the SNYK_GROUP_ID environment variable."
        )
    url = f"{_api_base()}/v1/org"
    body: dict = {"name": name, "groupId": group_id}
    if source_org_id:
        body["sourceOrgId"] = source_org_id
    resp = requests.post(url, json=body, headers=_auth_header(), timeout=30)
    if not resp.ok:
        detail = resp.text
        try:
            detail = resp.json()
        except Exception:
            pass
        raise RuntimeError(
            f"Failed to create org '{name}' (HTTP {resp.status_code}): {detail}"
        )
    return resp.json()


def get_integration_id(org_id: str, integration_type: str) -> str | None:
    """Look up the integration ID for an org + type.

    Returns ``None`` when the integration is not configured (HTTP 404)
    so the caller can collect all failures and report them together.
    Raises on unexpected errors (auth, server, etc.).
    """
    url = f"{_api_base()}/v1/org/{org_id}/integrations/{integration_type}"
    resp = requests.get(url, headers=_auth_header(), timeout=30)
    if resp.status_code == 404:
        return None
    if not resp.ok:
        detail = resp.text
        try:
            detail = resp.json()
        except Exception:
            pass
        raise RuntimeError(
            f"Error looking up '{integration_type}' integration for org {org_id} "
            f"(HTTP {resp.status_code}): {detail}"
        )
    data = resp.json()
    int_id = data.get("id")
    if not int_id:
        return None
    return int_id
