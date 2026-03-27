#!/usr/bin/env python3
"""
Generate a CSV of project, repo, developer username/email, and organization
from the Snyk Asset Search API at group scope.

Uses:
  POST /rest/groups/{group_id}/assets/search  (returns AssetAttributes with developers[])
  GET  /rest/groups/{group_id}/assets/{asset_id}/relationships/projects

Prereqs:
- Python 3.8+
- `pip install requests`
- SNYK_TOKEN in env (or pass --token)
"""

import argparse
import csv
import json
import os
import sys
from typing import Dict, Generator, List, Optional, Tuple

import requests

DEFAULT_VERSION = "2024-10-15"
FALLBACK_VERSIONS = ["2025-09-28", "2024-10-15~beta", "2025-09-28~beta"]
DEFAULT_BASE_URL = "https://api.snyk.io/rest"
API_ORIGIN = "https://api.snyk.io"


def build_session(token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {token}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/json",
    })
    return session


def _raise_with_body(resp: requests.Response) -> None:
    """Raise HTTPError with the response body printed for debugging."""
    sys.stderr.write(f"HTTP {resp.status_code} for {resp.url}\n")
    try:
        sys.stderr.write(f"Response: {resp.text[:2000]}\n")
    except Exception:
        pass
    resp.raise_for_status()


def _try_raw_post(session: requests.Session, url: str, params: Dict, body: Dict, timeout: int) -> Optional[Dict]:
    """Attempt a raw POST ignoring strict Accept header, returning parsed JSON or None."""
    headers = dict(session.headers)
    headers["Accept"] = "application/json"
    resp = session.post(url, params=params, json=body, timeout=timeout, headers=headers)
    if resp.ok:
        try:
            return resp.json()
        except Exception:
            return None
    return None


def _absolute_url(link: str, base_url: str) -> str:
    """Ensure a link is absolute by prepending the origin if it's a relative path."""
    if link.startswith("http"):
        return link
    origin = base_url.split("/rest")[0] if "/rest" in base_url else base_url.rstrip("/")
    return origin + link


def paged_post(
    session: requests.Session,
    url: str,
    params: Dict,
    body: Dict,
    timeout: int,
    base_url: str = DEFAULT_BASE_URL,
) -> Generator[Dict, None, None]:
    """Yield items from a JSON:API POST collection, following pagination links."""
    while True:
        resp = session.post(url, params=params, json=body, timeout=timeout)
        if not resp.ok:
            _raise_with_body(resp)
        payload = resp.json()
        for item in payload.get("data", []):
            yield item
        next_link = payload.get("links", {}).get("next")
        if not next_link:
            break
        url = _absolute_url(next_link, base_url)
        params = {}
        body = {}


def paged_get(
    session: requests.Session,
    url: str,
    params: Dict,
    timeout: int,
    base_url: str = DEFAULT_BASE_URL,
) -> Generator[Dict, None, None]:
    """Yield items from a JSON:API GET collection, following pagination links."""
    while True:
        resp = session.get(url, params=params, timeout=timeout)
        if not resp.ok:
            _raise_with_body(resp)
        payload = resp.json()
        for item in payload.get("data", []):
            yield item
        next_link = payload.get("links", {}).get("next")
        if not next_link:
            break
        url = _absolute_url(next_link, base_url)
        params = {}


def search_assets(
    session: requests.Session,
    base_url: str,
    group_id: str,
    version: str,
    timeout: int,
    asset_type_filter: Optional[str] = None,
    dump_first: bool = False,
) -> Generator[Dict, None, None]:
    """POST /groups/{group_id}/assets/search — returns AssetResponseData with developers[]."""
    url = f"{base_url}/groups/{group_id}/assets/search"

    body: Dict = {}
    if asset_type_filter:
        body = {
            "query": {
                "attributes": {
                    "attribute": "type",
                    "operator": "equal",
                    "values": [asset_type_filter],
                }
            }
        }

    versions_to_try = [version] + [v for v in FALLBACK_VERSIONS if v != version]

    last_exc = None
    for i, v in enumerate(versions_to_try):
        params = {"version": v}
        try:
            first = True
            for item in paged_post(session, url, params, body, timeout, base_url):
                if dump_first and first:
                    try:
                        sys.stderr.write(f"Using API version: {v}\n")
                        sys.stderr.write("First asset payload (truncated):\n")
                        sys.stderr.write(json.dumps(item, indent=2)[:4000] + "\n")
                    except Exception:
                        pass
                    first = False
                yield item
            return
        except requests.HTTPError as exc:
            last_exc = exc
            is_last = (i == len(versions_to_try) - 1)
            if exc.response is not None and exc.response.status_code in (500, 404) and not is_last:
                next_v = versions_to_try[i + 1]
                sys.stderr.write(f"Version {v} returned {exc.response.status_code}; trying {next_v}...\n")
                continue
            if exc.response is not None and exc.response.status_code == 500:
                sys.stderr.write("All versions returned 500. Trying raw Accept: application/json...\n")
                raw = _try_raw_post(session, url, {"version": version}, body, timeout)
                if raw and raw.get("data"):
                    for item in raw["data"]:
                        if dump_first:
                            sys.stderr.write("First asset (raw fallback):\n")
                            sys.stderr.write(json.dumps(item, indent=2)[:4000] + "\n")
                            dump_first = False
                        yield item
                    return
            raise


def normalize_repo(attrs: Dict) -> Optional[str]:
    """Best-effort repo identifier from AssetAttributes."""
    for key in ("repository_url", "browse_url", "name", "url"):
        val = attrs.get(key)
        if val:
            return val
    return None


def extract_orgs(asset: Dict) -> List[Dict]:
    """Extract inline organization data from asset relationships."""
    rels = asset.get("relationships") or {}
    orgs_rel = rels.get("organizations") or {}
    return orgs_rel.get("data") or []


def collect_rows(
    session: requests.Session,
    base_url: str,
    group_id: str,
    version: str,
    timeout: int,
    asset_type_filter: Optional[str],
    dedupe: bool,
    debug: bool,
    dump_first: bool,
    skip_empty: bool = False,
    max_assets: Optional[int] = None,
) -> List[Dict[str, Optional[str]]]:
    rows: List[Dict[str, Optional[str]]] = []
    seen: set = set()
    assets_seen = 0
    assets_with_devs = 0
    assets_skipped = 0

    for asset in search_assets(session, base_url, group_id, version, timeout, asset_type_filter, dump_first):
        assets_seen += 1
        if debug and assets_seen % 50 == 0:
            sys.stderr.write(f"  ...processed {assets_seen} assets so far ({len(rows)} rows)\n")
        if max_assets and assets_seen > max_assets:
            sys.stderr.write(f"Reached --max-assets limit ({max_assets}), stopping.\n")
            break

        attrs = asset.get("attributes") or {}
        developers = attrs.get("developers") or []
        repo = normalize_repo(attrs)
        asset_name = attrs.get("name")
        asset_id = asset.get("id")
        if not asset_id:
            continue
        if developers:
            assets_with_devs += 1

        orgs = extract_orgs(asset)
        org_names = [
            (o.get("attributes") or {}).get("name") for o in orgs
        ] or [None]

        if skip_empty and (not developers or not orgs):
            assets_skipped += 1
            continue

        for org_name in org_names:
            for dev in developers:
                row = {
                    "project": asset_name,
                    "repo": repo,
                    "developer.username": dev.get("username"),
                    "developer.email": dev.get("email"),
                    "organization": org_name,
                }
                if dedupe:
                    key = tuple(sorted(row.items()))
                    if key in seen:
                        continue
                    seen.add(key)
                rows.append(row)

    if debug:
        sys.stderr.write(
            f"Debug: assets_seen={assets_seen}, assets_with_devs={assets_with_devs}, assets_skipped={assets_skipped}, rows={len(rows)}\n"
        )
        if assets_seen == 0:
            sys.stderr.write(
                "No assets returned. Check group-id, region/base-url, token permissions, and version.\n"
            )
    return rows


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export developers by project/repo for a Snyk group via the Asset Search API."
    )
    parser.add_argument("--group-id", required=True, help="Snyk group ID (UUID).")
    parser.add_argument(
        "--token", default=os.getenv("SNYK_TOKEN"),
        help="Snyk API token (or set SNYK_TOKEN env var).",
    )
    parser.add_argument(
        "--base-url", default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL}).",
    )
    parser.add_argument(
        "--version", default=DEFAULT_VERSION,
        help=f"API version (default: {DEFAULT_VERSION}).",
    )
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--asset-type", default=None,
        choices=["repository", "image", "package"],
        help="Filter assets by type (default: all types).",
    )
    parser.add_argument("--max-assets", type=int, default=None, help="Stop after processing N assets (default: no limit).")
    parser.add_argument("--output", default="-", help="Output CSV path or '-' for stdout.")
    parser.add_argument("--dedupe", action="store_true", help="De-duplicate identical rows.")
    parser.add_argument(
        "--skip-empty", action="store_true",
        help="Skip assets with no developers or organizations.",
    )
    parser.add_argument("--debug", action="store_true", help="Print debug counts to stderr.")
    parser.add_argument(
        "--dump-first", action="store_true",
        help="Print the first asset payload to stderr for debugging.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if not args.token:
        sys.stderr.write("Missing token: set SNYK_TOKEN or pass --token\n")
        return 1

    session = build_session(args.token)
    base_url = args.base_url.rstrip("/")

    rows = collect_rows(
        session=session,
        base_url=base_url,
        group_id=args.group_id,
        version=args.version,
        timeout=args.timeout,
        asset_type_filter=args.asset_type,
        dedupe=args.dedupe,
        debug=args.debug,
        dump_first=args.dump_first,
        skip_empty=args.skip_empty,
        max_assets=args.max_assets,
    )

    fieldnames = ["project", "repo", "developer.username", "developer.email", "organization"]
    out_fp = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")
    with out_fp:
        writer = csv.DictWriter(out_fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    sys.stderr.write(f"Wrote {len(rows)} rows to {args.output}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
