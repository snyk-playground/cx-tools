#!/usr/bin/env python3
"""
Bulk rename Snyk organizations using the Snyk REST API.
PATCH /rest/orgs/{org_id}?version=2024-10-15
"""

from __future__ import annotations

import argparse
import csv
import email.utils
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

import requests

# Retry behavior aligned with
# https://github.com/sam1el/deactivate-reactivate-all-projects (429 + Retry-After;
# 5xx uses pysnyk-style tries/delay/backoff since we use raw requests).

API_VERSION = "2024-10-15"
DEFAULT_BASE = "https://api.snyk.io"
LOG_FILENAME = "rename_log.csv"


def normalize_optional_group_id(raw: str | None) -> str | None:
    """
    REST GET /rest/orgs accepts query param group_id (UUID).
    Returns None if unset/blank; raises ValueError if non-blank but not a UUID.
    """
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    try:
        return str(uuid.UUID(s))
    except ValueError as e:
        raise ValueError("--group-id must be a UUID") from e


def orgs_list_url(base_url: str, group_id: str | None) -> str:
    """First-page GET /rest/orgs URL with optional group_id filter."""
    params: dict[str, str] = {"version": API_VERSION}
    if group_id:
        params["group_id"] = group_id
    q = urlencode(params)
    return f"{base_url.rstrip('/')}/rest/orgs?{q}"


@dataclass(frozen=True)
class RetryConfig:
    """HTTP retry policy for Snyk REST calls."""

    rate_limit_max_attempts: int = 8
    server_error_max_attempts: int = 5
    server_error_initial_delay: float = 2.0
    server_error_backoff: float = 2.0


def _retry_after_seconds(retry_after: str | None) -> float:
    """
    Parse Retry-After (seconds or HTTP-date) into a sleep duration.
    Default 60s if missing or unparsable (same idea as pysnyk / common clients).
    """
    if not retry_after:
        return 60.0
    value = retry_after.strip()
    if value.isdigit():
        return float(value)
    try:
        dt: datetime | None = None
        if hasattr(email.utils, "parsedate_to_datetime"):
            dt = email.utils.parsedate_to_datetime(value)  # type: ignore[assignment]
        if dt is None:
            tup = email.utils.parsedate(value)
            if tup:
                dt = datetime(
                    tup[0],
                    tup[1],
                    tup[2],
                    tup[3],
                    tup[4],
                    tup[5],
                    tzinfo=timezone.utc,
                )
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = (dt - datetime.now(timezone.utc)).total_seconds()
            return max(0.1, float(delta))
    except (TypeError, ValueError, OverflowError):
        pass
    return 60.0


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"token {token}",
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
    }


def _request_single(
    session: requests.Session,
    method: str,
    url: str,
    *,
    token: str,
    json_body: dict[str, Any] | None = None,
) -> requests.Response:
    kwargs: dict[str, Any] = {
        "headers": _headers(token),
        "timeout": 120,
    }
    if json_body is not None:
        kwargs["json"] = json_body
    return session.request(method, url, **kwargs)


def _trusted_snyk_host(hostname: str) -> bool:
    h = (hostname or "").lower()
    return h == "snyk.io" or h.endswith(".snyk.io")


def validate_api_base(url: str) -> str:
    """Ensure API base URL is https and uses an official *.snyk.io host."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("API base URL must use https")
    if not _trusted_snyk_host(parsed.hostname or ""):
        raise ValueError(
            "API base URL hostname must be *.snyk.io (e.g. https://api.snyk.io)",
        )
    return url.rstrip("/")


def resolve_pagination_url(next_url: str, base_url: str) -> str:
    """Resolve relative next links and refuse cross-host pagination (SSRF-safe)."""
    base_parsed = urlparse(base_url)
    base_netloc = base_parsed.netloc
    if next_url.startswith("http"):
        parsed = urlparse(next_url)
        if parsed.scheme != "https":
            raise RuntimeError("Pagination URL must use https")
        if (parsed.hostname or "").lower() != (base_parsed.hostname or "").lower():
            raise RuntimeError("Pagination link points to a different host; refusing.")
        return next_url
    origin = f"{base_parsed.scheme}://{base_netloc}"
    return origin.rstrip("/") + "/" + next_url.lstrip("/")


def sanitize_csv_cell(value: str) -> str:
    """Reduce CSV formula-injection risk when logs are opened in spreadsheets."""
    if not value:
        return value
    if value[0] in "=-+@\t\r":
        return "'" + value
    return value


def format_csv_log_line(fields: list[str]) -> str:
    """RFC 4180 CSV row with neutralized fields (avoids spreadsheet formula injection)."""
    parts: list[str] = []
    for raw in fields:
        safe = sanitize_csv_cell(raw)
        escaped = safe.replace('"', '""')
        parts.append(f'"{escaped}"')
    return ",".join(parts) + "\n"


def request_until_not_rate_limited(
    session: requests.Session,
    method: str,
    url: str,
    *,
    token: str,
    json_body: dict[str, Any] | None,
    retry: RetryConfig,
) -> requests.Response:
    """
    Retry loop for consecutive HTTP 429, honoring Retry-After (seconds or HTTP-date).
    Matches sam1el/deactivate-reactivate-all-projects RateLimitAwareSnykClient semantics.
    """
    rate_limit_count = 0
    while True:
        response = _request_single(session, method, url, token=token, json_body=json_body)
        if response.status_code != 429:
            return response
        rate_limit_count += 1
        if rate_limit_count > retry.rate_limit_max_attempts:
            logging.warning(
                "HTTP 429: exceeded --rate-limit-attempts (%s); returning last response.",
                retry.rate_limit_max_attempts,
            )
            return response
        wait = _retry_after_seconds(response.headers.get("Retry-After"))
        logging.warning(
            "HTTP 429 rate limited; sleeping %.1fs (%s/%s consecutive 429s before giving up)...",
            wait,
            rate_limit_count,
            retry.rate_limit_max_attempts,
        )
        time.sleep(wait)


def request_with_retry(
    session: requests.Session,
    method: str,
    url: str,
    *,
    token: str,
    json_body: dict[str, Any] | None = None,
    retry: RetryConfig | None = None,
) -> requests.Response:
    """
    REST request with:
    - repeated attempts on consecutive 429 (Retry-After aware),
    - exponential backoff on 5xx (same defaults as pysnyk: tries=5, delay=2, backoff=2).
    """
    cfg = retry or RetryConfig()
    last_response: requests.Response | None = None
    for server_attempt in range(cfg.server_error_max_attempts):
        last_response = request_until_not_rate_limited(
            session,
            method,
            url,
            token=token,
            json_body=json_body,
            retry=cfg,
        )
        code = last_response.status_code
        if not (500 <= code < 600):
            return last_response
        if server_attempt + 1 >= cfg.server_error_max_attempts:
            return last_response
        wait = cfg.server_error_initial_delay * (
            cfg.server_error_backoff**server_attempt
        )
        logging.warning(
            "HTTP %s; transient server error — backing off %.1fs then retry (%s/%s)...",
            code,
            wait,
            server_attempt + 1,
            cfg.server_error_max_attempts,
        )
        time.sleep(wait)
    assert last_response is not None
    return last_response


def fetch_all_orgs(
    session: requests.Session,
    base_url: str,
    token: str,
    retry: RetryConfig,
    group_id: str | None = None,
) -> list[dict[str, str]]:
    """GET /rest/orgs with pagination via links.next; optional group_id filters to one group."""
    orgs: list[dict[str, str]] = []
    url = orgs_list_url(base_url, group_id)
    while url:
        r = request_with_retry(session, "GET", url, token=token, retry=retry)
        if r.status_code >= 400:
            raise RuntimeError(f"Failed to list orgs: HTTP {r.status_code}: {r.text[:500]}")
        payload = r.json()
        for item in payload.get("data") or []:
            oid = item.get("id", "")
            attrs = item.get("attributes") or {}
            name = attrs.get("name") or ""
            orgs.append({"id": oid, "name": name})
        links = payload.get("links") or {}
        next_url = links.get("next")
        if not next_url:
            break
        url = resolve_pagination_url(next_url, base_url)
    return orgs


def get_org_name(
    session: requests.Session,
    base_url: str,
    token: str,
    org_id: str,
    retry: RetryConfig,
) -> str | None:
    """GET /rest/orgs/{org_id}; return current name or None on failure."""
    url = f"{base_url.rstrip('/')}/rest/orgs/{org_id}?version={API_VERSION}"
    r = request_with_retry(session, "GET", url, token=token, retry=retry)
    if r.status_code >= 400:
        return None
    try:
        payload = r.json()
        data = payload.get("data") or {}
        attrs = data.get("attributes") or {}
        return attrs.get("name")
    except (json.JSONDecodeError, TypeError, AttributeError):
        return None


def patch_org_name(
    session: requests.Session,
    base_url: str,
    token: str,
    org_id: str,
    new_name: str,
    retry: RetryConfig,
) -> requests.Response:
    url = f"{base_url.rstrip('/')}/rest/orgs/{org_id}?version={API_VERSION}"
    body = {
        "data": {
            "attributes": {"name": new_name},
            "id": org_id,
            "type": "org",
        }
    }
    return request_with_retry(session, "PATCH", url, token=token, json_body=body, retry=retry)


def extract_error_message(response: requests.Response) -> str:
    try:
        data = response.json()
        errors = data.get("errors") or []
        if errors:
            parts = []
            for err in errors:
                detail = err.get("detail") or err.get("title") or json.dumps(err)
                parts.append(str(detail))
            return "; ".join(parts) if parts else response.text[:500]
    except (json.JSONDecodeError, ValueError):
        pass
    return (response.text or "")[:500]


def apply_pattern(pattern: str, org_id: str, old_name: str) -> str:
    return pattern.replace("{id}", org_id).replace("{name}", old_name)


def read_mapping_csv(path: str) -> dict[str, str]:
    path = str(Path(path).expanduser().resolve())
    mapping: dict[str, str] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        field_map = {(h or "").strip().lower(): h for h in reader.fieldnames}
        id_key = field_map.get("org_id") or field_map.get("id")
        name_key = field_map.get("new_name") or field_map.get("name")
        if not id_key or not name_key:
            raise ValueError("Mapping CSV must contain columns org_id and new_name (or id and name)")
        for row in reader:
            oid = (row.get(id_key) or "").strip()
            new_n = (row.get(name_key) or "").strip()
            if oid and new_n:
                mapping[oid] = new_n
    return mapping


def write_log_row(
    path: str,
    org_id: str,
    old_name: str,
    new_name: str,
    status: str,
    error_message: str,
) -> None:
    line = format_csv_log_line([org_id, old_name, new_name, status, error_message])
    with open(path, "a", newline="", encoding="utf-8") as f:
        f.write(line)


def run_csv_mode(
    args: argparse.Namespace,
    session: requests.Session,
    token: str,
    log_path: str,
) -> tuple[int, int, int]:
    succeeded = failed = skipped = 0
    pending: list[tuple[str, str]] = []
    csv_path = str(Path(args.file).expanduser().resolve())
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            logging.error("CSV has no header row.")
            return 0, 0, 0
        lower = [h.strip().lower() if h else "" for h in reader.fieldnames]
        try:
            i_org = lower.index("org_id")
            i_name = lower.index("new_name")
        except ValueError:
            logging.error("CSV must include columns: org_id, new_name")
            return 0, 0, 0
        cols = list(reader.fieldnames)
        for row in reader:
            oid = (row.get(cols[i_org]) or "").strip()
            new_n = (row.get(cols[i_name]) or "").strip()
            if not oid or not new_n:
                logging.warning("Skipping row with missing org_id or new_name: %s", row)
                skipped += 1
                write_log_row(
                    log_path,
                    oid or "",
                    "",
                    new_n,
                    "skipped",
                    "missing org_id or new_name",
                )
                continue
            pending.append((oid, new_n))

    if args.dry_run:
        for oid, new_n in pending:
            print(f"[dry-run] would rename org {oid} -> {new_n!r}")
            write_log_row(log_path, oid, "", new_n, "dry_run", "")
            succeeded += 1
        return succeeded, failed, skipped

    for oid, new_n in pending:
        old_name = get_org_name(session, args.base_url, token, oid, args.retry)
        if old_name is None:
            err = "could not load current org name (GET failed)"
            logging.error("Org %s: %s", oid, err)
            write_log_row(log_path, oid, "", new_n, "failed", err)
            failed += 1
            continue
        if old_name == new_n:
            logging.info("Skipping %s — name already %r.", oid, new_n)
            skipped += 1
            write_log_row(log_path, oid, old_name, new_n, "skipped", "unchanged")
            continue
        r = patch_org_name(session, args.base_url, token, oid, new_n, args.retry)
        if r.status_code in (200, 201, 204):
            write_log_row(log_path, oid, old_name, new_n, "success", "")
            succeeded += 1
            logging.info("Renamed org %s from %r to %r", oid, old_name, new_n)
        else:
            err = extract_error_message(r)
            write_log_row(log_path, oid, old_name, new_n, "failed", err)
            failed += 1
            logging.error("Failed to rename org %s: HTTP %s — %s", oid, r.status_code, err)

    return succeeded, failed, skipped


def run_export_mode(
    args: argparse.Namespace,
    session: requests.Session,
    token: str,
) -> tuple[int, int, int]:
    """
    GET all orgs and write a CSV template: org_id,new_name with new_name = current name.
    User edits the file, then runs --mode csv --file <path> to apply.
    """
    orgs = fetch_all_orgs(
        session,
        args.base_url,
        token,
        args.retry,
        group_id=args.group_id,
    )
    out_path = str(Path(args.file).expanduser().resolve())
    if args.dry_run:
        scope = f" group={args.group_id}" if args.group_id else ""
        print(f"[dry-run] would write {len(orgs)} rows to {out_path}{scope}")
        for o in orgs:
            print(f"  {o['id']}\t{o['name']!r}")
        return len(orgs), 0, 0

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        f.write(format_csv_log_line(["org_id", "new_name"]))
        for o in orgs:
            f.write(format_csv_log_line([o["id"], o["name"]]))

    scope = f" (group {args.group_id})" if args.group_id else ""
    print(f"Wrote {len(orgs)} row(s) to: {out_path}{scope}")
    print(
        "Edit the new_name column for any orgs you want to rename "
        "(leave unchanged names as-is — they will be skipped on apply). Then run:\n"
        f"  python snyk_bulk_org_rename.py --mode csv --file {out_path}",
    )
    return len(orgs), 0, 0


def prompt_pull_options() -> tuple[str | None, str | None]:
    """Returns (mapping_path, pattern)."""
    map_path = input(
        "Path to mapping CSV (columns org_id, new_name), or press Enter to use a pattern: ",
    ).strip()
    if map_path:
        return map_path, None
    pattern = input(
        "Naming pattern (use {name} for current name, {id} for org id), e.g. 'TEAM-{name}': ",
    ).strip()
    if not pattern:
        print("Error: provide either a mapping file or a non-empty pattern.", file=sys.stderr)
        sys.exit(2)
    return None, pattern


def run_pull_mode(
    args: argparse.Namespace,
    session: requests.Session,
    token: str,
    log_path: str,
) -> tuple[int, int, int]:
    succeeded = failed = skipped = 0

    if args.dry_run:
        logging.warning(
            "Pull mode with --dry-run: GET /rest/orgs still runs to list orgs; "
            "PATCH (rename) calls are skipped.",
        )

    orgs = fetch_all_orgs(
        session,
        args.base_url,
        token,
        args.retry,
        group_id=args.group_id,
    )
    if not orgs:
        print("No organizations returned for this token (check --group-id and permissions).")
        return 0, 0, 0

    filter_note = f" (group {args.group_id})" if args.group_id else ""
    print(f"\nOrganizations (id → name){filter_note}:")
    print("-" * 60)
    for o in orgs:
        print(f"  {o['id']}\t{o['name']}")
    print("-" * 60)
    print(f"Total: {len(orgs)}\n")

    mp = args.mapping
    pat = args.pattern
    if mp and pat:
        logging.info("Both --mapping and --pattern set; using --mapping.")
        pat = None
    if not mp and not pat:
        if not sys.stdin.isatty():
            print(
                "Non-interactive mode: use --mapping or --pattern for pull mode.",
                file=sys.stderr,
            )
            sys.exit(2)
        mp, pat = prompt_pull_options()

    mapping: dict[str, str] = {}
    if mp:
        mapping = read_mapping_csv(mp)
        if not mapping:
            logging.error("Mapping file is empty or has no valid rows.")
            return 0, 0, 0

    operations: list[tuple[str, str, str]] = []
    for o in orgs:
        oid, old_name = o["id"], o["name"]
        if mp:
            if oid not in mapping:
                logging.warning("No mapping for org %s; skipping.", oid)
                skipped += 1
                write_log_row(log_path, oid, old_name, "", "skipped", "not in mapping file")
                continue
            new_name = mapping[oid]
        else:
            assert pat is not None
            new_name = apply_pattern(pat, oid, old_name)
        if new_name == old_name:
            logging.info("Skipping %s — name unchanged.", oid)
            skipped += 1
            write_log_row(log_path, oid, old_name, new_name, "skipped", "unchanged")
            continue
        operations.append((oid, old_name, new_name))

    if args.dry_run:
        for oid, old_name, new_name in operations:
            print(f"[dry-run] would rename {oid} ({old_name!r}) -> {new_name!r}")
            write_log_row(log_path, oid, old_name, new_name, "dry_run", "")
            succeeded += 1
        return succeeded, failed, skipped

    for oid, old_name, new_name in operations:
        r = patch_org_name(session, args.base_url, token, oid, new_name, args.retry)
        if r.status_code in (200, 201, 204):
            write_log_row(log_path, oid, old_name, new_name, "success", "")
            succeeded += 1
            logging.info("Renamed org %s from %r to %r", oid, old_name, new_name)
        else:
            err = extract_error_message(r)
            write_log_row(log_path, oid, old_name, new_name, "failed", err)
            failed += 1
            logging.error("Failed org %s: HTTP %s — %s", oid, r.status_code, err)

    return succeeded, failed, skipped


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bulk rename Snyk organizations via the REST API.",
    )
    parser.add_argument(
        "--mode",
        choices=("csv", "pull", "export"),
        required=True,
        help=(
            "csv: apply renames from CSV; export: write CSV template from API then edit & use csv; "
            "pull: list orgs and rename via mapping or pattern"
        ),
    )
    parser.add_argument(
        "--file",
        help=(
            "CSV path: required for --mode csv (input) and --mode export (output template); "
            "see README"
        ),
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SNYK_API_URL", DEFAULT_BASE),
        metavar="URL",
        help=f"https API host under *.snyk.io (default: {DEFAULT_BASE} or SNYK_API_URL)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "csv: no API calls. export: print planned rows, do not write file. "
            "pull: GET org list but skip PATCH."
        ),
    )
    parser.add_argument(
        "--log-file",
        default=LOG_FILENAME,
        help=f"CSV log output path (default: {LOG_FILENAME})",
    )
    parser.add_argument(
        "--mapping",
        help="(pull mode) CSV mapping with org_id and new_name (non-interactive)",
    )
    parser.add_argument(
        "--pattern",
        help=r"(pull mode) Naming pattern with {name} and {id} (non-interactive)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument(
        "--rate-limit-attempts",
        type=int,
        default=8,
        metavar="N",
        help=(
            "Max consecutive HTTP 429 responses per API request before giving up "
            "(default: 8). Sleeps use Retry-After when present (seconds or HTTP-date)."
        ),
    )
    parser.add_argument(
        "--group-id",
        metavar="UUID",
        default=None,
        help=(
            "Only list orgs in this Snyk group (REST query group_id on GET /rest/orgs). "
            "Useful for export/pull when your token sees many groups. "
            "Also set via SNYK_GROUP_ID."
        ),
    )
    args = parser.parse_args()

    if args.rate_limit_attempts < 1:
        parser.error("--rate-limit-attempts must be at least 1")

    raw_group = args.group_id or os.environ.get("SNYK_GROUP_ID")
    try:
        args.group_id = normalize_optional_group_id(raw_group)
    except ValueError as e:
        parser.error(str(e))

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    token = os.environ.get("SNYK_TOKEN", "").strip()
    if not token:
        print("SNYK_TOKEN environment variable is required.", file=sys.stderr)
        sys.exit(2)

    if args.mode in ("csv", "export") and not args.file:
        parser.error(f"--mode {args.mode} requires --file")

    try:
        args.base_url = validate_api_base(args.base_url)
    except ValueError as e:
        parser.error(str(e))

    args.retry = RetryConfig(rate_limit_max_attempts=args.rate_limit_attempts)

    session = requests.Session()

    try:
        if args.mode == "export":
            succeeded, failed, skipped = run_export_mode(args, session, token)
            print(
                f"\nSummary: rows_written={succeeded}, failed={failed}, skipped={skipped}",
            )
            return
        log_path = str(Path(args.log_file).expanduser().resolve())
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            f.write(
                format_csv_log_line(
                    ["org_id", "old_name", "new_name", "status", "error_message"],
                ),
            )

        if args.mode == "csv":
            succeeded, failed, skipped = run_csv_mode(args, session, token, log_path)
        else:
            succeeded, failed, skipped = run_pull_mode(args, session, token, log_path)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)

    print(
        f"\nSummary: succeeded={succeeded}, failed={failed}, skipped={skipped}\n"
        f"Log written to: {log_path}",
    )


if __name__ == "__main__":
    main()
