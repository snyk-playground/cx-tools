import argparse
import concurrent.futures
import email.utils
import os
import sys
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
import snyk
from snyk.client import SnykClient
from snyk.errors import SnykHTTPError
from yaspin import yaspin

TOKEN_ERROR_HINT = (
    "Ran into an error while fetching account details; check your API token "
    "or OAuth credentials and network access."
)

# Mirrors `snyk config environment` regional URL mappings (see Snyk regional hosting docs).
ENVIRONMENT_PRESETS: Dict[str, Dict[str, str]] = {
    "SNYK-US-01": {
        "api_url": "https://api.snyk.io/v1",
        "rest_api_url": "https://api.snyk.io/rest",
        "oauth_token_url": "https://api.snyk.io/oauth2/token",
    },
    "SNYK-US-02": {
        "api_url": "https://api.us.snyk.io/v1",
        "rest_api_url": "https://api.us.snyk.io/rest",
        "oauth_token_url": "https://api.us.snyk.io/oauth2/token",
    },
    "SNYK-EU-01": {
        "api_url": "https://api.eu.snyk.io/v1",
        "rest_api_url": "https://api.eu.snyk.io/rest",
        "oauth_token_url": "https://api.eu.snyk.io/oauth2/token",
    },
    "SNYK-AU-01": {
        "api_url": "https://api.au.snyk.io/v1",
        "rest_api_url": "https://api.au.snyk.io/rest",
        "oauth_token_url": "https://api.au.snyk.io/oauth2/token",
    },
    "SNYK-GOV-01": {
        "api_url": "https://api.snykgov.io/v1",
        "rest_api_url": "https://api.snykgov.io/rest",
        "oauth_token_url": "https://api.snykgov.io/oauth2/token",
    },
}


def _retry_after_seconds(retry_after: Optional[str]) -> float:
    """Parse Retry-After (seconds or HTTP-date) into a sleep duration."""
    if not retry_after:
        return 60.0
    value = retry_after.strip()
    if value.isdigit():
        return float(value)
    try:
        dt = None
        if hasattr(email.utils, "parsedate_to_datetime"):
            dt = email.utils.parsedate_to_datetime(value)  # Python 3.10+
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


def _normalize_api_v1_url(url: str) -> str:
    u = url.strip().rstrip("/")
    if not u.endswith("/v1"):
        u = f"{u}/v1"
    return u


def _oauth_token_url_from_api_v1(api_v1_url: str) -> str:
    """https://api.example/v1 -> https://api.example/oauth2/token"""
    base = api_v1_url.strip().rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return f"{base}/oauth2/token"


def _assert_trusted_snyk_https_url(url: str, what: str) -> str:
    """
    Restrict configurable endpoints to known Snyk hostnames over HTTPS so
    user-supplied URLs cannot be abused for SSRF against internal networks.
    Set SNYK_ALLOW_UNVERIFIED_API_URL=1 to skip hostname checks (single-tenant / nonstandard hosts).
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise SystemExit(f"{what} must use an https:// URL.")
    host = (parsed.hostname or "").lower()
    if not host:
        raise SystemExit(f"{what} must include a valid hostname.")

    if os.environ.get("SNYK_ALLOW_UNVERIFIED_API_URL") == "1":
        return url

    if host.endswith(".snyk.io") or host.endswith(".snykgov.io"):
        return url

    raise SystemExit(
        f"{what} hostname {host!r} is not under *.snyk.io or *.snykgov.io. "
        "If your tenant uses another hostname, set SNYK_ALLOW_UNVERIFIED_API_URL=1 "
        "(still requires HTTPS)."
    )


def _fetch_oauth_access_token(
    token_url: str,
    client_id: str,
    client_secret: str,
    *,
    verify: bool = True,
) -> Dict[str, Any]:
    resp = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        verify=verify,
        timeout=120,
    )
    if not resp.ok:
        raise SnykHTTPError(resp)
    return resp.json()


class RateLimitAwareSnykClient(snyk.SnykClient):
    """
    Extends pysnyk's client: retries on HTTP 429 using Retry-After, and sets
    sensible defaults for transient 5xx retries (pysnyk only retries when
    request() raises, which excludes 429).
    """

    def __init__(
        self,
        token: str,
        *,
        rate_limit_max_attempts: int = 8,
        **kwargs,
    ):
        kwargs.setdefault("tries", 5)
        kwargs.setdefault("delay", 2)
        kwargs.setdefault("backoff", 2)
        super().__init__(token, **kwargs)
        self.rate_limit_max_attempts = rate_limit_max_attempts

    def request(
        self,
        method,
        url: str,
        headers: object,
        params: object = None,
        json: object = None,
    ) -> requests.Response:
        rate_limit_count = 0
        while True:
            if params and json:
                resp = method(
                    url,
                    headers=headers,
                    params=params,
                    json=json,
                    verify=self.verify,
                )
            elif params and not json:
                resp = method(
                    url, headers=headers, params=params, verify=self.verify
                )
            elif json and not params:
                resp = method(url, headers=headers, json=json, verify=self.verify)
            else:
                resp = method(url, headers=headers, verify=self.verify)

            if resp.status_code == 429:
                rate_limit_count += 1
                if rate_limit_count > self.rate_limit_max_attempts:
                    raise SnykHTTPError(resp)
                wait = _retry_after_seconds(resp.headers.get("Retry-After"))
                time.sleep(wait)
                continue

            if not resp or resp.status_code >= requests.codes.server_error:
                raise SnykHTTPError(resp)
            return resp


class OAuthRateLimitAwareSnykClient(RateLimitAwareSnykClient):
    """
    Uses Authorization: Bearer <access_token> (required for OAuth2 service accounts).
    pysnyk defaults to ``Authorization: token <api_key>``; OAuth access tokens need Bearer.

    With client_id + client_secret, fetches and refreshes tokens via the OAuth2 token endpoint
    before they expire (client_credentials grant).
    """

    _OAUTH_REFRESH_SKEW_SEC = 60.0

    def __init__(
        self,
        token: str,
        *,
        use_bearer: bool,
        oauth_client_id: Optional[str] = None,
        oauth_client_secret: Optional[str] = None,
        oauth_token_url: Optional[str] = None,
        **kwargs,
    ):
        self._use_bearer = use_bearer
        self._oauth_client_id = oauth_client_id
        self._oauth_client_secret = oauth_client_secret
        self._oauth_token_url = oauth_token_url or ""
        self._access_expires_at: float = 0.0
        init_token = token
        if use_bearer and oauth_client_id and oauth_client_secret and not (token or "").strip():
            init_token = "oauth-pending"
        super().__init__(init_token, **kwargs)
        if self._use_bearer:
            if self._oauth_client_credentials():
                self._ensure_fresh_oauth_token()
            else:
                if not self.api_token.strip():
                    raise SystemExit(
                        "OAuth bearer mode requires SNYK_OAUTH_TOKEN or "
                        "SNYK_OAUTH_CLIENT_ID and SNYK_OAUTH_CLIENT_SECRET."
                    )
                self._apply_bearer_headers()

    def _apply_bearer_headers(self) -> None:
        auth = f"Bearer {self.api_token}"
        ua = self.api_headers.get("User-Agent", SnykClient.USER_AGENT)
        self.api_headers = {"Authorization": auth, "User-Agent": ua}
        self.api_post_headers = {
            **self.api_headers,
            "Content-Type": "application/json",
        }

    def _apply_api_key_headers(self) -> None:
        auth = f"token {self.api_token}"
        ua = self.api_headers.get("User-Agent", SnykClient.USER_AGENT)
        self.api_headers = {"Authorization": auth, "User-Agent": ua}
        self.api_post_headers = {
            **self.api_headers,
            "Content-Type": "application/json",
        }

    def _oauth_client_credentials(self) -> bool:
        return bool(self._oauth_client_id and self._oauth_client_secret)

    def _ensure_fresh_oauth_token(self) -> None:
        if not self._oauth_client_credentials():
            return
        if self.api_token and self.api_token != "oauth-pending":
            if time.monotonic() < self._access_expires_at - self._OAUTH_REFRESH_SKEW_SEC:
                return
        if not self._oauth_token_url:
            raise SystemExit(
                "OAuth client credentials are set but the token URL is missing. "
                "Set SNYK_OAUTH_TOKEN_URL or use --environment / --oauth-token-url."
            )
        body = _fetch_oauth_access_token(
            self._oauth_token_url,
            self._oauth_client_id or "",
            self._oauth_client_secret or "",
            verify=self.verify,
        )
        access = body.get("access_token")
        if not access or not isinstance(access, str):
            raise SystemExit("OAuth token response did not include a usable access_token.")
        self.api_token = access
        expires_in = body.get("expires_in")
        if expires_in is not None:
            try:
                self._access_expires_at = time.monotonic() + float(expires_in)
            except (TypeError, ValueError):
                self._access_expires_at = time.monotonic() + 3600.0
        else:
            self._access_expires_at = time.monotonic() + 3600.0
        self._apply_bearer_headers()

    def request(
        self,
        method,
        url: str,
        headers: object,
        params: object = None,
        json: object = None,
    ) -> requests.Response:
        if self._use_bearer:
            self._ensure_fresh_oauth_token()
        resp = super().request(method, url, headers, params, json)
        if (
            resp.status_code == 401
            and self._oauth_client_credentials()
            and self._use_bearer
        ):
            self._access_expires_at = 0.0
            self._ensure_fresh_oauth_token()
            resp = super().request(method, url, headers, params, json)
        return resp


def _parse_allowed_origins(args: argparse.Namespace) -> Optional[Set[str]]:
    """
    Build the set of project origins to include (Snyk project `origin` field).
    --origin may be repeated; --origins adds more in one token group.
    If none given, all origins are processed.
    """
    parts = []
    if args.origin:
        parts.extend(args.origin)
    if args.origins:
        parts.extend(args.origins)
    if not parts:
        return None
    return {p.strip().casefold() for p in parts if p.strip()}


def _should_process_project(origin: str, allowed: Optional[Set[str]]) -> bool:
    if allowed is None:
        return True
    return origin.casefold() in allowed


def inactive_projects_in_org(
    org: Any,
    allowed_origins: Optional[Set[str]],
) -> List[Any]:
    """
    Projects in the organization that match the origin filter and are inactive
    (Snyk isMonitored is False: not monitored / deactivated in the UI).
    """
    return [
        p
        for p in org.projects.all()
        if _should_process_project(p.origin, allowed_origins) and not p.isMonitored
    ]


def _org_matches_token(org: Any, token: str) -> bool:
    """True if token is this org's id (UUID) or slug (case-insensitive)."""
    t = token.strip()
    if org.id == t:
        return True
    return org.slug.casefold() == t.casefold()


def _create_snyk_client(
    args: argparse.Namespace,
    urls: Dict[str, str],
    *,
    interactive_token: Optional[str] = None,
) -> Any:
    """
    Build a Snyk client from CLI args, resolved URLs, and environment.
    ``interactive_token`` is only used when no OAuth/API env credentials are set.
    """
    env_name = urls["environment"]
    client_kw = {
        "url": urls["api_url"],
        "rest_api_url": urls["rest_api_url"],
        "rate_limit_max_attempts": args.rate_limit_attempts,
    }
    oauth_client_id = os.environ.get("SNYK_OAUTH_CLIENT_ID")
    oauth_client_secret = os.environ.get("SNYK_OAUTH_CLIENT_SECRET")
    oauth_access = os.environ.get("SNYK_OAUTH_TOKEN")
    api_key = os.environ.get("SNYK_TOKEN")

    if oauth_client_id and oauth_client_secret:
        return OAuthRateLimitAwareSnykClient(
            "",
            use_bearer=True,
            oauth_client_id=oauth_client_id,
            oauth_client_secret=oauth_client_secret,
            oauth_token_url=urls["oauth_token_url"],
            **client_kw,
        )
    if oauth_access:
        return OAuthRateLimitAwareSnykClient(
            oauth_access,
            use_bearer=True,
            **client_kw,
        )
    if api_key:
        if env_name == "SNYK-GOV-01":
            print(
                "Snyk for Government (FedRAMP) does not support static API tokens; "
                "use OAuth2 service account credentials (SNYK_OAUTH_CLIENT_ID and "
                "SNYK_OAUTH_CLIENT_SECRET) or a short-lived SNYK_OAUTH_TOKEN.",
                file=sys.stderr,
            )
            raise SystemExit(1)
        return RateLimitAwareSnykClient(api_key, **client_kw)
    if env_name == "SNYK-GOV-01":
        raise SystemExit(
            "FedRAMP / Snyk for Government requires OAuth2. Set "
            "SNYK_OAUTH_CLIENT_ID and SNYK_OAUTH_CLIENT_SECRET (recommended), or "
            "SNYK_OAUTH_TOKEN for a short-lived access token. "
            "Static SNYK_TOKEN is not allowed."
        )
    if interactive_token is None:
        raise SystemExit(
            "No Snyk credentials in environment (SNYK_TOKEN or OAuth variables)."
        )
    return RateLimitAwareSnykClient(interactive_token.strip(), **client_kw)


def _post_project_state_change(
    client: Any, org_id: str, project_id: str, verb: str
) -> bool:
    """POST deactivate or activate (matches pysnyk Project.activate/deactivate paths)."""
    path = f"org/{org_id}/project/{project_id}/{verb}"
    return bool(client.post(path, {}))


class _ThreadLocalClientHolder:
    """One Snyk client per worker thread (OAuth refresh and requests are not shared)."""

    def __init__(self, args: argparse.Namespace, urls: Dict[str, str]) -> None:
        self._args = args
        self._urls = urls
        self._local = threading.local()

    def get(self) -> Any:
        client = getattr(self._local, "client", None)
        if client is None:
            self._local.client = _create_snyk_client(self._args, self._urls)
        return self._local.client


def _project_work_row(p: Any) -> Tuple[str, str, str, str, str, bool]:
    return (
        p.organization.id,
        p.id,
        p.name,
        p.origin,
        p.type,
        p.isMonitored,
    )


def _run_parallel_project_posts(
    holder: _ThreadLocalClientHolder,
    rows: List[Tuple[str, str, str, str, str, bool]],
    verb: str,
    *,
    workers: int,
    verbose: bool,
    log_lock: threading.Lock,
    count_truthy_ok: bool,
) -> Tuple[int, List[str]]:
    """
    Run deactivate or activate for many projects in parallel.
    Returns (success_count, error_messages).

    When ``count_truthy_ok`` is True (activate), increments success for truthy POST results,
    matching ``if ok: total_projects_cycled += 1`` in the sequential path.
    When False (deactivate), any completed POST without an exception counts as success
    (the sequential path does not treat a falsy body as failure).
    """
    successes = 0
    errors: List[str] = []

    def _one(row: Tuple[str, str, str, str, str, bool]) -> Tuple[bool, Optional[str]]:
        org_id, project_id, name, origin, typ, is_monitored = row
        try:
            c = holder.get()
            if verbose:
                with log_lock:
                    print(
                        f"    [verbose] POST {verb} project id={project_id} "
                        f"isMonitored={is_monitored!r} origin={origin!r}"
                    )
            ok = _post_project_state_change(c, org_id, project_id, verb)
            if verbose:
                with log_lock:
                    print(f"    [verbose] {verb} response ok={ok!r}")
            if count_truthy_ok:
                return ok, None
            return True, None
        except Exception as err:
            return False, f"{name} ({verb}): {err}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_one, row) for row in rows]
        for fut in concurrent.futures.as_completed(futures):
            ok, err = fut.result()
            if err:
                with log_lock:
                    print(f"\u001b[31m    {err}\u001b[0m")
                errors.append(err)
            elif ok:
                successes += 1
    return successes, errors


def _resolve_urls(args: argparse.Namespace) -> Dict[str, str]:
    """API v1 base, REST base, and OAuth2 token URL for this run."""
    env_name = (
        getattr(args, "environment", None)
        or os.environ.get("SNYK_ENVIRONMENT")
        or "SNYK-US-01"
    )
    preset = ENVIRONMENT_PRESETS.get(env_name)
    if not preset:
        raise SystemExit(f"Unknown environment {env_name!r}; use one of the known presets.")

    api = getattr(args, "api_url", None) or os.environ.get("SNYK_API_URL") or preset["api_url"]
    api = _normalize_api_v1_url(api)

    rest = (
        getattr(args, "rest_api_url", None)
        or os.environ.get("SNYK_REST_API_URL")
        or preset["rest_api_url"]
    ).rstrip("/")

    oauth_token_url = (
        getattr(args, "oauth_token_url", None)
        or os.environ.get("SNYK_OAUTH_TOKEN_URL")
        or preset.get("oauth_token_url")
        or _oauth_token_url_from_api_v1(api)
    )
    _assert_trusted_snyk_https_url(api, "API v1 URL")
    _assert_trusted_snyk_https_url(rest, "REST API URL")
    _assert_trusted_snyk_https_url(oauth_token_url, "OAuth token URL")

    return {
        "environment": env_name,
        "api_url": api,
        "rest_api_url": rest,
        "oauth_token_url": oauth_token_url,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Deactivate and reactivate Snyk projects to rebuild SCM webhooks, "
            "or with --activate-inactive-only only activate projects that are already inactive. "
            "Optionally limit to projects with specific Snyk project origins "
            "(SCM / import source, e.g. github, github-cloud-app, gitlab)."
        )
    )
    parser.add_argument(
        "--orgs",
        nargs="*",
        default=None,
        help=(
            "Organization slug(s) and/or org id(s) (UUID from Snyk settings). "
            "If omitted, you will be prompted."
        ),
    )
    parser.add_argument(
        "--origin",
        action="append",
        default=None,
        metavar="ORIGIN",
        help=(
            "Only process projects with this Snyk project origin (repeat for "
            "several). Examples: github, github-cloud-app (GitHub App imports), "
            "github-enterprise, gitlab, bitbucket-cloud, azure-repos. "
            "Use the exact string the API returns (see dry-run). "
            "Omit to include all origins."
        ),
    )
    parser.add_argument(
        "--origins",
        nargs="+",
        metavar="ORIGIN",
        help=(
            "Same as repeating --origin: only these project origins (space-separated)."
        ),
    )
    parser.add_argument(
        "--rate-limit-attempts",
        type=int,
        default=8,
        metavar="N",
        help="Max consecutive HTTP 429 responses to retry per request (default: 8).",
    )
    parser.add_argument(
        "--environment",
        default=os.environ.get("SNYK_ENVIRONMENT"),
        choices=sorted(ENVIRONMENT_PRESETS.keys()),
        metavar="NAME",
        help=(
            "Snyk region/instance (same idea as `snyk config environment`). "
            "Use SNYK-GOV-01 for Snyk for Government (FedRAMP). "
            "Defaults to SNYK-US-01 when SNYK_ENVIRONMENT is unset."
        ),
    )
    parser.add_argument(
        "--api-url",
        metavar="URL",
        help=(
            "Override API v1 base URL (e.g. https://api.snykgov.io/v1). "
            "Also set via SNYK_API_URL."
        ),
    )
    parser.add_argument(
        "--rest-api-url",
        metavar="URL",
        help="Override REST API base URL. Also set via SNYK_REST_API_URL.",
    )
    parser.add_argument(
        "--oauth-token-url",
        metavar="URL",
        help=(
            "OAuth2 token endpoint (…/oauth2/token). Default is derived from the API URL. "
            "Also set via SNYK_OAUTH_TOKEN_URL."
        ),
    )
    parser.add_argument(
        "--activate-inactive-only",
        action="store_true",
        help=(
            "Only activate projects that are currently inactive (not monitored). "
            "Skips deactivate entirely; does not touch already-active projects. "
            "Same origin filters as without this flag."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "List organizations and projects that would be cycled; do not call "
            "deactivate or activate. Still requires valid credentials to list data."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help=(
            "Print environment/API endpoints, which organizations the token can see, "
            "and per-project API details (id, monitored flag, result). Use when results "
            "in the Snyk UI are unclear or something seems skipped."
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        metavar="N",
        help=(
            "Parallel HTTP workers for deactivate/activate (default: 1, fully sequential). "
            "Try 8–16 for large orgs; higher values increase throughput but may trigger "
            "more HTTP 429 responses (retries still apply). When N>1, credentials must come "
            "from the environment (SNYK_TOKEN or OAuth variables), not an interactive prompt."
        ),
    )
    args = parser.parse_args()

    if args.workers < 1:
        raise SystemExit("--workers must be >= 1")
    if args.workers > 64:
        raise SystemExit("--workers cannot exceed 64")

    allowed_origins = _parse_allowed_origins(args)
    input_orgs = list(args.orgs) if args.orgs else []

    urls = _resolve_urls(args)
    env_name = urls["environment"]

    oauth_client_id = os.environ.get("SNYK_OAUTH_CLIENT_ID")
    oauth_client_secret = os.environ.get("SNYK_OAUTH_CLIENT_SECRET")
    oauth_access = os.environ.get("SNYK_OAUTH_TOKEN")
    api_key = os.environ.get("SNYK_TOKEN")
    has_env_creds = bool(
        (oauth_client_id and oauth_client_secret) or oauth_access or api_key
    )
    if args.workers > 1 and not has_env_creds:
        raise SystemExit(
            "--workers > 1 requires SNYK_TOKEN or OAuth credentials in the environment; "
            "interactive API token entry is not supported with parallel workers."
        )

    interactive_token: Optional[str] = None
    if not has_env_creds:
        print("Enter your Snyk API Token")
        interactive_token = input()

    client = _create_snyk_client(args, urls, interactive_token=interactive_token)

    user_orgs = []
    try:
        user_orgs = client.organizations.all()
    except SnykHTTPError:
        print(f"💥 {TOKEN_ERROR_HINT}")
        raise SystemExit(1)

    if args.verbose:
        print(
            f"\n[verbose] environment={env_name!r} api_v1={urls['api_url']!r} "
            f"rest={urls['rest_api_url']!r} oauth={urls['oauth_token_url']!r}\n"
            f"[verbose] this token can see {len(user_orgs)} organization(s):"
        )
        for o in user_orgs:
            print(f"  - id={o.id} slug={o.slug!r} name={o.name!r}")
        print()

    if not input_orgs:
        if args.activate_inactive_only:
            prompt = (
                "to preview which inactive projects would be activated"
                if args.dry_run
                else "to activate inactive (not monitored) projects only"
            )
        else:
            prompt = (
                "to preview which projects would be cycled (deactivate + reactivate)"
                if args.dry_run
                else "to reactivate projects to generate webhooks"
            )
        print(f"Input the org slug(s) or org id(s) (UUID) for which you would like {prompt}.")
        input_orgs = input().split()

    total_projects_cycled = 0
    for curr_org in user_orgs:
        matched = [t for t in input_orgs if _org_matches_token(curr_org, t)]
        if not matched:
            continue
        for t in matched:
            input_orgs.remove(t)
        if args.dry_run:
            if args.activate_inactive_only:
                dry_intro = (
                    "projects listed below are inactive (not monitored) and would be "
                    "activated only (no deactivate)."
                )
            else:
                dry_intro = (
                    "projects listed below are what would be deactivated, then reactivated."
                )
            print(
                "\n\u001b[1;33m[DRY-RUN]\u001b[0m No API changes will be made for organization "
                f'\033[1;32m"{curr_org.name}"\u001b[0m ({dry_intro})\n'
            )
        else:
            print(
                "Processing"
                + """ \033[1;32m"{}" """.format(curr_org.name)
                + "\u001b[0morganization"
            )

        if args.activate_inactive_only:
            projects = inactive_projects_in_org(curr_org, allowed_origins)
        else:
            projects = [
                p
                for p in curr_org.projects.all()
                if _should_process_project(p.origin, allowed_origins)
            ]

        if args.verbose:
            filt = (
                "inactive + origin filters"
                if args.activate_inactive_only
                else "origin filter"
            )
            print(
                f"[verbose] matched org: id={curr_org.id} slug={curr_org.slug!r} "
                f'name="{curr_org.name}" — {len(projects)} project(s) after {filt}\n'
            )

        if not args.dry_run and not projects:
            if args.activate_inactive_only:
                warn_detail = (
                    "No inactive (not monitored) projects matched the origin filter (if any). "
                    "No activate was called"
                )
            else:
                warn_detail = (
                    "No projects to process in this org after applying the origin filter (if any). "
                    "No deactivate/activate was called"
                )
            print(
                f"\n\u001b[1;33mWARNING\u001b[0m: {warn_detail} for "
                f"organization \"{curr_org.name}\" (id {curr_org.id}). "
                "If that is unexpected, check \u001b[1m--origins\u001b[0m, "
                "\u001b[1m--environment\u001b[0m (region), and that the org has imported projects.\n"
            )
        if args.dry_run and projects:
            if args.activate_inactive_only:
                summary = (
                    f"{len(projects)} inactive project(s) would be activated in this org."
                )
            else:
                summary = f"{len(projects)} project(s) would be cycled in this org."
            print(f"  \u001b[90m{summary}\u001b[0m")
        elif args.dry_run:
            if args.activate_inactive_only:
                msg = "No inactive projects match the origin filter (if any) in this org."
            else:
                msg = "No projects match the origin filter (if any) in this org."
            print(f"  \u001b[90m{msg}\u001b[0m")

        log_lock = threading.Lock()
        parallel_holder: Optional[_ThreadLocalClientHolder] = None
        if not args.dry_run and args.workers > 1 and projects:
            parallel_holder = _ThreadLocalClientHolder(args, urls)
            mode_hint = (
                "activate only"
                if args.activate_inactive_only
                else "deactivate and activate"
            )
            print(
                f"    Using \033[1;33m{args.workers}\u001b[0m concurrent worker(s) for "
                f"{mode_hint} ({len(projects)} project(s))."
            )

        if not args.activate_inactive_only:
            if args.dry_run:
                for curr_project in projects:
                    curr_project_details = (
                        f"Origin: {curr_project.origin}, Type: {curr_project.type}"
                    )
                    print(
                        f"    [DRY-RUN] would deactivate: \u001b[1;33m{curr_project.name}\u001b[0m  "
                        f"(\u001b[34m{curr_project_details}\u001b[0m)"
                    )
            elif args.workers > 1 and parallel_holder is not None:
                rows = [_project_work_row(p) for p in projects]
                _run_parallel_project_posts(
                    parallel_holder,
                    rows,
                    "deactivate",
                    workers=args.workers,
                    verbose=args.verbose,
                    log_lock=log_lock,
                    count_truthy_ok=False,
                )
            else:
                for curr_project in projects:
                    curr_project_details = (
                        f"Origin: {curr_project.origin}, Type: {curr_project.type}"
                    )
                    action = "Deactivating"
                    spinner = yaspin(
                        text=f"{action}\033[1;33m {curr_project.name}", color="yellow"
                    )
                    spinner.write(
                        f"\u001b[0m    Processing project: \u001b[34m{curr_project_details}\u001b[0m, Status Below👇"
                    )
                    spinner.start()
                    try:
                        if args.verbose:
                            print(
                                f"    [verbose] POST deactivate project id={curr_project.id} "
                                f"isMonitored={curr_project.isMonitored!r} origin={curr_project.origin!r}"
                            )
                        ok = curr_project.deactivate()
                        if args.verbose:
                            print(f"    [verbose] deactivate response ok={ok!r}")
                        spinner.ok("🆗 ")
                    except Exception as err:
                        spinner.fail("💥 ")
                        spinner.write(f"\u001b[31m    {err}\u001b[0m")

        if args.dry_run:
            for curr_project in projects:
                curr_project_details = (
                    f"Origin: {curr_project.origin}, Type: {curr_project.type}"
                )
                label = (
                    "would activate (inactive)"
                    if args.activate_inactive_only
                    else "would reactivate"
                )
                print(
                    f"    [DRY-RUN] {label}: \u001b[1;32m{curr_project.name}\u001b[0m  "
                    f"(\u001b[34m{curr_project_details}\u001b[0m)"
                )
        elif args.workers > 1 and parallel_holder is not None:
            rows = [_project_work_row(p) for p in projects]
            n_ok, _ = _run_parallel_project_posts(
                parallel_holder,
                rows,
                "activate",
                workers=args.workers,
                verbose=args.verbose,
                log_lock=log_lock,
                count_truthy_ok=True,
            )
            total_projects_cycled += n_ok
        else:
            for curr_project in projects:
                curr_project_details = (
                    f"Origin: {curr_project.origin}, Type: {curr_project.type}"
                )
                action = "Activating"
                spinner = yaspin(
                    text=f"{action}\033[1;32m {curr_project.name}", color="yellow"
                )
                spinner.write(
                    f"\u001b[0m    Processing project: \u001b[34m{curr_project_details}\u001b[0m, Status Below👇"
                )
                spinner.start()
                try:
                    if args.verbose:
                        print(
                            f"    [verbose] POST activate project id={curr_project.id} "
                            f"isMonitored={curr_project.isMonitored!r} origin={curr_project.origin!r}"
                        )
                    ok = curr_project.activate()
                    if args.verbose:
                        print(f"    [verbose] activate response ok={ok!r}")
                    if ok:
                        total_projects_cycled += 1
                    spinner.ok("🆗 ")
                except Exception as err:
                    spinner.fail("💥 ")
                    spinner.write(f"\u001b[31m    {err}\u001b[0m")

    if input_orgs:
        print(
            "\033[1;32m{}\u001b[0m are organizations which do not exist or you "
            "don't have access to them; check spelling, use dashes instead of "
            "spaces, and use org slugs or org id (UUID) from Snyk.".format(
                input_orgs
            )
        )

    if not args.dry_run and not input_orgs and total_projects_cycled == 0:
        # All requested org names were matched, but no activate returned success (0 projects, or errors).
        print(
            "\n\u001b[1;33mNote\u001b[0m: no successful \u001b[1mactivate\u001b[0m in this run. If you "
            "expected projects, re-check region (\u001b[1m--environment\u001b[0m), org slug/UUID, "
            "and \u001b[1m--origins\u001b[0m; use \u001b[1m--verbose\u001b[0m to show API details.\n"
        )

if __name__ == "__main__":
    main()
