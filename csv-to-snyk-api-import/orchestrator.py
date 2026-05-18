"""
Orchestration helpers that combine API calls with the converter logic:
org resolution / creation and integration-ID lookup.
"""

from converter import (
    _org_id_for_row,
    resolve_integration_type_for_url,
)
from snyk_api import create_org, get_integration_id, list_orgs


def resolve_org_ids(
    rows: list[dict],
    group_id: str,
    template_org_id: str | None,
) -> dict[str, str]:
    """Ensure every row has a usable org ID.

    Returns a mapping of ``snyk_org_name -> snyk_org_id`` for any names that
    had to be resolved or created.  Rows that already carry an org ID are
    left untouched (and not included in the returned mapping).
    """
    # Collect unique names that need resolution.
    names_to_resolve: set[str] = set()
    for row in rows:
        org_id = (row.get("snyk_org_id") or "").strip()
        org_name = (row.get("snyk_org_name") or "").strip()
        if not org_id and org_name:
            names_to_resolve.add(org_name)

    if not names_to_resolve:
        return {}

    # Fetch existing orgs once.
    existing_orgs = list_orgs()
    name_to_id: dict[str, str] = {}
    for org in existing_orgs:
        org_name_existing = org.get("name", "")
        if org_name_existing in names_to_resolve:
            name_to_id[org_name_existing] = org["id"]

    # Create any that don't exist yet.
    for name in sorted(names_to_resolve):
        if name not in name_to_id:
            print(f"  Creating Snyk org '{name}' …")
            try:
                new_org = create_org(name, group_id, template_org_id)
            except (RuntimeError, ValueError) as exc:
                raise RuntimeError(
                    f"Failed to create org '{name}': {exc}"
                ) from exc
            name_to_id[name] = new_org["id"]
            print(f"  Created org '{name}' → {new_org['id']}")

    return name_to_id


def resolve_integration_ids(
    rows: list[dict],
    name_to_org_id: dict[str, str],
    host_to_integration: dict[str, str] | None = None,
) -> dict[tuple[str, str], str]:
    """For every unique (org_id, integration_type) pair, look up the
    integration ID.  Returns a mapping of (org_id, type) → integration_id.

    Collects all missing integrations and raises a single error listing
    every (org, type) pair that needs attention.
    """
    h2i = host_to_integration or {}
    pairs: set[tuple[str, str]] = set()
    for row in rows:
        org_id = _org_id_for_row(row, name_to_org_id)
        integration_type = resolve_integration_type_for_url(
            row["repo_url"].strip(), h2i
        )
        pairs.add((org_id, integration_type))

    result: dict[tuple[str, str], str] = {}
    missing: list[tuple[str, str]] = []
    for org_id, integration_type in sorted(pairs):
        print(f"  Looking up integration '{integration_type}' for org {org_id} …")
        int_id = get_integration_id(org_id, integration_type)
        if int_id is None:
            print(f"  ✗ Not found")
            missing.append((org_id, integration_type))
        else:
            result[(org_id, integration_type)] = int_id
            print(f"  Found integration {int_id}")

    if missing:
        lines = "\n".join(
            f"  • org {org_id}  →  {itype}" for org_id, itype in missing
        )
        raise RuntimeError(
            f"The following integration(s) are not configured:\n{lines}\n\n"
            f"To fix this, go to each org's Settings → Integrations in the "
            f"Snyk UI and enable the required integration.\n"
            f"If you are using SNYK_TEMPLATE_ORG_ID to create orgs, make sure "
            f"the template org has all needed integrations configured."
        )

    return result
