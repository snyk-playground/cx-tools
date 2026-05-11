"""
CLI entry point – reads args, orchestrates the pipeline, writes JSON output,
and optionally kicks off snyk-api-import.
"""

import json
import os
import shutil
import subprocess
import sys

from converter import (
    KNOWN_INTEGRATION_TYPES,
    build_import_json,
    detect_integration_type,
    hostname_from_url,
    read_csv,
    validate_rows,
)
from orchestrator import resolve_integration_ids, resolve_org_ids

DEFAULT_LOG_PATH = "./logs"


def resolve_unknown_hosts(rows: list[dict]) -> dict[str, str]:
    """Find repo URLs whose hostname can't be auto-detected and ask the user
    to choose an integration type.  Returns a mapping of hostname → type.
    """
    unknown_hosts: dict[str, str] = {}  # hostname → first example URL
    for row in rows:
        url = (row.get("repo_url") or "").strip()
        if not url:
            continue
        if detect_integration_type(url) is not None:
            continue
        host = hostname_from_url(url)
        unknown_hosts.setdefault(host, url)

    if not unknown_hosts:
        return {}

    numbered = list(KNOWN_INTEGRATION_TYPES)
    menu = "\n".join(f"  {i + 1}) {t}" for i, t in enumerate(numbered))

    host_to_integration: dict[str, str] = {}
    for host, example_url in unknown_hosts.items():
        print(f"\nUnrecognised hostname: {host}")
        print(f"  Example URL: {example_url}")
        print(f"Which Snyk integration type should be used?\n{menu}")
        while True:
            choice = input("Enter number: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(numbered):
                selected = numbered[int(choice) - 1]
                host_to_integration[host] = selected
                print(f"  → {host} mapped to '{selected}'")
                break
            print(f"  Invalid choice. Enter a number between 1 and {len(numbered)}.")

    return host_to_integration


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]

    if not args:
        print("Usage: python3 csv_to_snyk_import.py <input.csv> [output.json]")
        sys.exit(1)

    csv_path = os.path.realpath(args[0])
    # Output file is always written to the current directory – strip any
    # directory components to prevent path-traversal via CLI arguments.
    output_filename = os.path.basename(
        args[1] if len(args) > 1 else "import-projects.json"
    )
    if not output_filename:
        output_filename = "import-projects.json"
    output_path = os.path.join(os.getcwd(), output_filename)

    # --- Environment ---
    group_id = os.environ.get("SNYK_GROUP_ID", "")
    template_org_id = os.environ.get("SNYK_TEMPLATE_ORG_ID")
    log_path = os.environ.get("SNYK_LOG_PATH", DEFAULT_LOG_PATH)

    missing: list[str] = []
    if not os.environ.get("SNYK_TOKEN"):
        missing.append("SNYK_TOKEN")
    if missing:
        for var in missing:
            print(f"Error: {var} environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # --- Phase 1: Read & validate CSV ---
    print(f"Reading CSV: {csv_path}")
    rows = read_csv(csv_path)
    validate_rows(rows)
    print(f"  {len(rows)} rows read and validated.")

    # Check SNYK_GROUP_ID if any row needs org creation.
    needs_org_creation = any(
        not (row.get("snyk_org_id") or "").strip()
        and (row.get("snyk_org_name") or "").strip()
        for row in rows
    )
    if needs_org_creation and not group_id:
        print(
            "Error: SNYK_GROUP_ID environment variable is required because "
            "one or more rows use 'snyk_org_name' (org creation).",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        # --- Phase 2: Resolve unknown hostnames ---
        host_to_integration = resolve_unknown_hosts(rows)

        # --- Phase 3: Org resolution / creation ---
        print("Resolving Snyk organisations …")
        name_to_org_id = resolve_org_ids(rows, group_id, template_org_id)
        if name_to_org_id:
            print(f"  Resolved {len(name_to_org_id)} org name(s) to IDs.")

        # --- Phase 4: Integration lookup ---
        print("Looking up integration IDs …")
        integration_cache = resolve_integration_ids(
            rows, name_to_org_id, host_to_integration
        )

        # --- Phase 5: Build JSON ---
        print("Building import-projects.json …")
        import_data = build_import_json(
            rows, name_to_org_id, integration_cache, host_to_integration
        )
    except (RuntimeError, ValueError, KeyError) as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(import_data, fh, indent=2)

    target_count = len(import_data["targets"])
    unique_orgs = {t["orgId"] for t in import_data["targets"]}
    print(
        f"\nGenerated {output_path} with {target_count} target(s) "
        f"across {len(unique_orgs)} org(s)."
    )

    # --- Phase 5: Prompt to run import ---
    import_cmd = f"snyk-api-import import --file={output_path}"

    if shutil.which("snyk-api-import") is None:
        print("\nsnyk-api-import is not installed or not on your PATH.")
        print("Install it from: https://github.com/snyk/snyk-api-import/releases")
        print("\nOnce installed, run:")
        print(f"  {import_cmd}")
        return

    answer = input("\nRun snyk-api-import now? [y/N] ").strip().lower()
    if answer in ("y", "yes"):
        env = os.environ.copy()
        env.setdefault("SNYK_LOG_PATH", log_path)
        # snyk-api-import expects SNYK_API to include /v1 at the end.
        snyk_api = env.get("SNYK_API", "https://api.snyk.io").rstrip("/")
        if not snyk_api.endswith("/v1"):
            snyk_api += "/v1"
        env["SNYK_API"] = snyk_api
        cmd = ["snyk-api-import", "import", f"--file={output_path}"]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, env=env, check=False)
    else:
        print("Skipped. You can run the import later with:")
        print(f"  {import_cmd}")


if __name__ == "__main__":
    main()
