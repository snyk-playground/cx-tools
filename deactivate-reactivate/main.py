import argparse
import email.utils
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional, Set

import requests
import snyk
from snyk.errors import SnykHTTPError
from yaspin import yaspin

TOKEN_ERROR_HINT = (
    "Ran into an error while fetching account details; check your API token "
    "and network access."
)


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


def _org_matches_token(org: Any, token: str) -> bool:
    """True if token is this org's id (UUID) or slug (case-insensitive)."""
    t = token.strip()
    if org.id == t:
        return True
    return org.slug.casefold() == t.casefold()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Deactivate and reactivate Snyk projects to rebuild SCM webhooks. "
            "Optionally limit to projects with specific Snyk project origins "
            "(SCM / import source, e.g. github, gitlab)."
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
            "several). Examples: github, github-enterprise, gitlab, "
            "bitbucket-cloud, azure-repos. Omit to include all origins."
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
    args = parser.parse_args()

    allowed_origins = _parse_allowed_origins(args)
    input_orgs = list(args.orgs) if args.orgs else []

    if "SNYK_TOKEN" in os.environ:
        snyk_token = os.environ["SNYK_TOKEN"]
    else:
        print("Enter your Snyk API Token")
        snyk_token = input()

    user_orgs = []
    client = RateLimitAwareSnykClient(
        snyk_token,
        rate_limit_max_attempts=args.rate_limit_attempts,
    )
    try:
        user_orgs = client.organizations.all()
    except SnykHTTPError:
        print(f"💥 {TOKEN_ERROR_HINT}")
        raise SystemExit(1)

    if not input_orgs:
        print(
            "Input the org slug(s) or org id(s) (UUID) for which you would like "
            "to reactivate projects to generate webhooks."
        )
        input_orgs = input().split()

    for curr_org in user_orgs:
        matched = [t for t in input_orgs if _org_matches_token(curr_org, t)]
        if not matched:
            continue
        for t in matched:
            input_orgs.remove(t)
        print(
            "Processing"
            + """ \033[1;32m"{}" """.format(curr_org.name)
            + "\u001b[0morganization"
        )

        projects = [
            p
            for p in curr_org.projects.all()
            if _should_process_project(p.origin, allowed_origins)
        ]

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
                curr_project.deactivate()
                spinner.ok("🆗 ")
            except Exception as err:
                spinner.fail("💥 ")
                spinner.write(f"\u001b[31m    {err}\u001b[0m")

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
                curr_project.activate()
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


if __name__ == "__main__":
    main()
