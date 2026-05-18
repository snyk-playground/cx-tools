"""
Tests for the CSV → import-projects.json transformation logic.

Focuses on pure functions in converter.py.
All Snyk API calls are mocked so tests run entirely offline.
"""

import csv
import json
import os
import tempfile
from unittest.mock import patch

import pytest

from converter import (
    DEFAULT_BRANCH,
    KNOWN_INTEGRATION_TYPES,
    build_import_json,
    build_import_target,
    build_target,
    detect_integration_type,
    hostname_from_url,
    parse_repo_url,
    read_csv,
    resolve_integration_type_for_url,
    validate_row,
    validate_rows,
)
from orchestrator import (
    resolve_integration_ids,
    resolve_org_ids,
)


# ======================================================================
# Helpers
# ======================================================================

def _write_csv(path: str, rows: list[dict]) -> None:
    """Write a list of dicts as a CSV file with a header row."""
    if not rows:
        # Write an empty file (no header, no data)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            pass
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _make_row(**overrides) -> dict:
    """Return a minimal valid CSV row dict, with optional overrides."""
    base = {
        "repo_url": "https://github.com/my-org/my-repo",
        "snyk_org_id": "org-id-123",
        "snyk_org_name": "",
        "branch": "",
        "exclusion_globs": "",
    }
    base.update(overrides)
    return base


# ======================================================================
# URL Parsing Tests
# ======================================================================


class TestParseRepoUrl:
    def test_github_standard(self):
        target = parse_repo_url("https://github.com/my-org/my-repo")
        assert target == {"owner": "my-org", "name": "my-repo"}

    def test_github_with_trailing_slash(self):
        target = parse_repo_url("https://github.com/my-org/my-repo/")
        assert target == {"owner": "my-org", "name": "my-repo"}

    def test_github_with_extra_path_segments(self):
        target = parse_repo_url("https://github.com/my-org/my-repo/tree/main")
        assert target == {"owner": "my-org", "name": "my-repo"}

    def test_azure_devops_standard(self):
        target = parse_repo_url(
            "https://dev.azure.com/my-org/my-project/_git/my-repo"
        )
        assert target == {"owner": "my-org/my-project", "name": "my-repo"}

    def test_azure_devops_with_trailing_slash(self):
        target = parse_repo_url(
            "https://dev.azure.com/my-org/my-project/_git/my-repo/"
        )
        assert target == {"owner": "my-org/my-project", "name": "my-repo"}

    def test_github_enterprise(self):
        target = parse_repo_url(
            "https://github.mycompany.com/eng/service-api", "github-enterprise"
        )
        assert target == {"owner": "eng", "name": "service-api"}

    def test_bitbucket_cloud(self):
        target = parse_repo_url("https://bitbucket.org/workspace/my-repo")
        assert target == {"owner": "workspace", "name": "my-repo"}

    def test_bitbucket_server_scm_url(self):
        target = parse_repo_url(
            "https://bb.company.com/scm/PROJ/my-repo.git", "bitbucket-server"
        )
        assert target == {"repoSlug": "my-repo", "projectKey": "PROJ"}

    def test_bitbucket_server_projects_url(self):
        target = parse_repo_url(
            "https://bb.company.com/projects/PROJ/repos/my-repo", "bitbucket-server"
        )
        assert target == {"repoSlug": "my-repo", "projectKey": "PROJ"}

    def test_bitbucket_server_invalid_url(self):
        with pytest.raises(ValueError, match="Bitbucket Server URL"):
            parse_repo_url(
                "https://bb.company.com/unknown/path", "bitbucket-server"
            )

    def test_git_suffix_stripped(self):
        target = parse_repo_url(
            "https://github.com/my-org/my-repo.git", "github"
        )
        assert target == {"owner": "my-org", "name": "my-repo"}

    def test_invalid_url_no_host(self):
        with pytest.raises(ValueError, match="Cannot parse hostname"):
            parse_repo_url("not-a-url")

    def test_github_missing_repo(self):
        with pytest.raises(ValueError, match="URL must follow"):
            parse_repo_url("https://github.com/only-org")

    def test_azure_missing_git_segment(self):
        with pytest.raises(ValueError, match="Azure DevOps URL must follow"):
            parse_repo_url("https://dev.azure.com/my-org/my-project/bad/my-repo")

    def test_azure_too_short(self):
        with pytest.raises(ValueError, match="Azure DevOps URL must follow"):
            parse_repo_url("https://dev.azure.com/my-org")


# ======================================================================
# Integration Type Detection Tests
# ======================================================================


class TestDetectIntegrationType:
    def test_github_dot_com(self):
        assert detect_integration_type("https://github.com/o/r") == "github"

    def test_azure_devops(self):
        url = "https://dev.azure.com/o/p/_git/r"
        assert detect_integration_type(url) == "azure-repos"

    def test_bitbucket_cloud(self):
        assert detect_integration_type("https://bitbucket.org/ws/repo") == "bitbucket-cloud"

    def test_unknown_host_returns_none(self):
        url = "https://github.example.com/o/r"
        assert detect_integration_type(url) is None

    def test_unknown_host_generic(self):
        url = "https://my-git-server.internal/o/r"
        assert detect_integration_type(url) is None

    def test_no_hostname_raises(self):
        with pytest.raises(ValueError, match="Cannot parse hostname"):
            detect_integration_type("://missing")


# ======================================================================
# CSV Validation Tests
# ======================================================================


class TestValidateRow:
    def test_valid_with_org_id(self):
        row = _make_row(snyk_org_id="abc", snyk_org_name="")
        validate_row(row, 1)  # should not raise

    def test_valid_with_org_name(self):
        row = _make_row(snyk_org_id="", snyk_org_name="My Org")
        validate_row(row, 1)

    def test_valid_with_both(self):
        row = _make_row(snyk_org_id="abc", snyk_org_name="My Org")
        validate_row(row, 1)

    def test_missing_both_org_fields(self):
        row = _make_row(snyk_org_id="", snyk_org_name="")
        with pytest.raises(ValueError, match="at least one of"):
            validate_row(row, 1)

    def test_missing_repo_url(self):
        row = _make_row(repo_url="")
        with pytest.raises(ValueError, match="repo_url"):
            validate_row(row, 1)


class TestValidateRows:
    def test_all_valid(self):
        rows = [_make_row(), _make_row(repo_url="https://dev.azure.com/o/p/_git/r")]
        validate_rows(rows)

    def test_empty_csv(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as fh:
            path = fh.name
        try:
            with pytest.raises(ValueError, match="empty"):
                read_csv(path)
        finally:
            os.unlink(path)

    def test_malformed_csv_missing_required_column(self):
        """A CSV that has no repo_url column at all."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
        ) as fh:
            fh.write("some_col,another_col\nval1,val2\n")
            path = fh.name
        try:
            rows = read_csv(path)
            with pytest.raises(ValueError, match="repo_url"):
                validate_rows(rows)
        finally:
            os.unlink(path)


class TestReadCsv:
    def test_reads_valid_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
        ) as fh:
            _write_csv(fh.name, [_make_row()])
            path = fh.name
        try:
            rows = read_csv(path)
            assert len(rows) == 1
            assert rows[0]["repo_url"] == "https://github.com/my-org/my-repo"
        finally:
            os.unlink(path)

    def test_empty_file_raises(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as fh:
            path = fh.name
        try:
            with pytest.raises(ValueError, match="empty"):
                read_csv(path)
        finally:
            os.unlink(path)


# ======================================================================
# Target JSON Generation Tests
# ======================================================================

# Shared fixtures for target-building tests.
_NAME_TO_ORG_ID: dict[str, str] = {"My Org": "resolved-org-id"}
_INTEGRATION_CACHE: dict[tuple[str, str], str] = {
    ("org-id-123", "github"): "int-gh-001",
    ("org-id-123", "azure-repos"): "int-az-001",
    ("org-id-123", "bitbucket-cloud"): "int-bb-001",
    ("org-id-123", "bitbucket-server"): "int-bbs-001",
    ("resolved-org-id", "github"): "int-gh-002",
    ("resolved-org-id", "azure-repos"): "int-az-002",
}
_HOST_TO_INTEGRATION: dict[str, str] = {
    "bb.company.com": "bitbucket-server",
}


class TestBuildTarget:
    def test_github(self):
        row = _make_row()
        assert build_target(row) == {"owner": "my-org", "name": "my-repo"}

    def test_azure(self):
        row = _make_row(repo_url="https://dev.azure.com/o/p/_git/r")
        assert build_target(row) == {"owner": "o/p", "name": "r"}

    def test_bitbucket_cloud(self):
        row = _make_row(repo_url="https://bitbucket.org/ws/repo")
        assert build_target(row) == {"owner": "ws", "name": "repo"}

    def test_bitbucket_server(self):
        row = _make_row(repo_url="https://bb.company.com/scm/PROJ/repo.git")
        assert build_target(row, "bitbucket-server") == {
            "repoSlug": "repo",
            "projectKey": "PROJ",
        }


class TestBuildImportTarget:
    def test_github_defaults(self):
        row = _make_row()
        entry = build_import_target(row, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert entry == {
            "orgId": "org-id-123",
            "integrationId": "int-gh-001",
            "target": {"owner": "my-org", "name": "my-repo", "branch": "main"},
        }

    def test_custom_branch(self):
        row = _make_row(branch="develop")
        entry = build_import_target(row, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert entry["target"]["branch"] == "develop"

    def test_default_branch_when_blank(self):
        row = _make_row(branch="")
        entry = build_import_target(row, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert entry["target"]["branch"] == DEFAULT_BRANCH

    def test_exclusion_globs_included(self):
        row = _make_row(exclusion_globs="fixtures, tests")
        entry = build_import_target(row, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert entry["exclusionGlobs"] == "fixtures, tests"

    def test_exclusion_globs_omitted_when_blank(self):
        row = _make_row(exclusion_globs="")
        entry = build_import_target(row, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert "exclusionGlobs" not in entry

    def test_azure_target(self):
        row = _make_row(repo_url="https://dev.azure.com/o/p/_git/r")
        entry = build_import_target(row, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert entry["orgId"] == "org-id-123"
        assert entry["integrationId"] == "int-az-001"
        assert entry["target"] == {"owner": "o/p", "name": "r", "branch": "main"}

    def test_org_resolved_by_name(self):
        row = _make_row(snyk_org_id="", snyk_org_name="My Org")
        entry = build_import_target(row, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert entry["orgId"] == "resolved-org-id"
        assert entry["integrationId"] == "int-gh-002"

    def test_bitbucket_cloud_target(self):
        row = _make_row(repo_url="https://bitbucket.org/ws/repo")
        entry = build_import_target(row, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert entry["orgId"] == "org-id-123"
        assert entry["integrationId"] == "int-bb-001"
        assert entry["target"] == {
            "owner": "ws",
            "name": "repo",
            "branch": "main",
        }

    def test_bitbucket_server_target(self):
        row = _make_row(repo_url="https://bb.company.com/scm/PROJ/repo.git")
        entry = build_import_target(
            row, _NAME_TO_ORG_ID, _INTEGRATION_CACHE, _HOST_TO_INTEGRATION
        )
        assert entry["orgId"] == "org-id-123"
        assert entry["integrationId"] == "int-bbs-001"
        assert entry["target"]["repoSlug"] == "repo"
        assert entry["target"]["projectKey"] == "PROJ"
        assert entry["target"]["branch"] == "main"


class TestBuildImportJson:
    def test_single_github_row(self):
        rows = [_make_row()]
        result = build_import_json(rows, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert "targets" in result
        assert len(result["targets"]) == 1
        assert result["targets"][0]["orgId"] == "org-id-123"

    def test_single_azure_row(self):
        rows = [_make_row(repo_url="https://dev.azure.com/o/p/_git/r")]
        result = build_import_json(rows, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert len(result["targets"]) == 1
        assert result["targets"][0]["target"]["owner"] == "o/p"

    def test_mixed_sources_multiple_orgs(self):
        rows = [
            _make_row(),
            _make_row(
                repo_url="https://dev.azure.com/o/p/_git/r",
                snyk_org_id="",
                snyk_org_name="My Org",
            ),
        ]
        result = build_import_json(rows, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert len(result["targets"]) == 2
        org_ids = {t["orgId"] for t in result["targets"]}
        assert org_ids == {"org-id-123", "resolved-org-id"}

    def test_multiple_rows_same_org(self):
        rows = [
            _make_row(repo_url="https://github.com/o/repo1"),
            _make_row(repo_url="https://github.com/o/repo2"),
        ]
        result = build_import_json(rows, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert len(result["targets"]) == 2
        assert all(t["orgId"] == "org-id-123" for t in result["targets"])

    def test_large_csv(self):
        """100+ rows should all appear in the output."""
        rows = [
            _make_row(repo_url=f"https://github.com/org/repo-{i}")
            for i in range(150)
        ]
        result = build_import_json(rows, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        assert len(result["targets"]) == 150

    def test_output_is_valid_json(self):
        rows = [_make_row()]
        result = build_import_json(rows, _NAME_TO_ORG_ID, _INTEGRATION_CACHE)
        # Roundtrip through JSON to ensure serialisability.
        dumped = json.dumps(result)
        loaded = json.loads(dumped)
        assert loaded == result


# ======================================================================
# End-to-End Transformation Tests (mocked API calls)
# ======================================================================


class TestEndToEnd:
    """Full CSV file → import-projects.json, with API calls mocked."""

    @patch("orchestrator.get_integration_id")
    @patch("orchestrator.list_orgs")
    @patch("orchestrator.create_org")
    def test_full_pipeline(self, mock_create, mock_list, mock_get_int):
        # Simulate: "Team Alpha" already exists, "Team Beta" needs creation.
        mock_list.return_value = [
            {"name": "Team Alpha", "id": "alpha-id"},
        ]
        mock_create.return_value = {"id": "beta-id", "name": "Team Beta"}

        mock_get_int.side_effect = lambda org_id, itype: {
            ("alpha-id", "github"): "int-alpha-gh",
            ("beta-id", "azure-repos"): "int-beta-az",
            ("existing-org", "github"): "int-existing-gh",
        }[(org_id, itype)]

        rows = [
            {
                "repo_url": "https://github.com/acme/app",
                "snyk_org_id": "",
                "snyk_org_name": "Team Alpha",
                "branch": "main",
                "exclusion_globs": "",
            },
            {
                "repo_url": "https://dev.azure.com/acme/proj/_git/svc",
                "snyk_org_id": "",
                "snyk_org_name": "Team Beta",
                "branch": "develop",
                "exclusion_globs": "tests, fixtures",
            },
            {
                "repo_url": "https://github.com/acme/lib",
                "snyk_org_id": "existing-org",
                "snyk_org_name": "",
                "branch": "",
                "exclusion_globs": "",
            },
        ]

        name_to_id = resolve_org_ids(rows, "group-1", "template-1")
        assert name_to_id == {"Team Alpha": "alpha-id", "Team Beta": "beta-id"}
        mock_create.assert_called_once_with("Team Beta", "group-1", "template-1")

        int_cache = resolve_integration_ids(rows, name_to_id)
        result = build_import_json(rows, name_to_id, int_cache)

        assert len(result["targets"]) == 3

        # Target 1: GitHub → Team Alpha
        t0 = result["targets"][0]
        assert t0["orgId"] == "alpha-id"
        assert t0["integrationId"] == "int-alpha-gh"
        assert t0["target"] == {"owner": "acme", "name": "app", "branch": "main"}
        assert "exclusionGlobs" not in t0

        # Target 2: Azure → Team Beta
        t1 = result["targets"][1]
        assert t1["orgId"] == "beta-id"
        assert t1["integrationId"] == "int-beta-az"
        assert t1["target"] == {
            "owner": "acme/proj",
            "name": "svc",
            "branch": "develop",
        }
        assert t1["exclusionGlobs"] == "tests, fixtures"

        # Target 3: GitHub → existing org
        t2 = result["targets"][2]
        assert t2["orgId"] == "existing-org"
        assert t2["integrationId"] == "int-existing-gh"
        assert t2["target"]["branch"] == DEFAULT_BRANCH

    @patch("orchestrator.get_integration_id")
    @patch("orchestrator.list_orgs")
    def test_csv_file_to_json_file(self, mock_list, mock_get_int):
        """Read from a real CSV file, produce a real JSON file."""
        mock_list.return_value = []
        mock_get_int.return_value = "int-id-999"

        row_data = [
            {
                "repo_url": "https://github.com/org-a/repo-1",
                "snyk_org_id": "org-aaa",
                "snyk_org_name": "",
                "branch": "release",
                "exclusion_globs": "node_modules",
            },
            {
                "repo_url": "https://github.com/org-a/repo-2",
                "snyk_org_id": "org-aaa",
                "snyk_org_name": "",
                "branch": "",
                "exclusion_globs": "",
            },
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
        ) as csv_fh:
            _write_csv(csv_fh.name, row_data)
            csv_path = csv_fh.name

        json_path = csv_path.replace(".csv", ".json")

        try:
            rows = read_csv(csv_path)
            validate_rows(rows)
            name_to_id: dict[str, str] = {}
            int_cache = resolve_integration_ids(rows, name_to_id)
            result = build_import_json(rows, name_to_id, int_cache)

            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(result, jf, indent=2)

            with open(json_path, encoding="utf-8") as jf:
                loaded = json.load(jf)

            assert loaded["targets"][0]["target"]["branch"] == "release"
            assert loaded["targets"][0]["exclusionGlobs"] == "node_modules"
            assert loaded["targets"][1]["target"]["branch"] == DEFAULT_BRANCH
            assert "exclusionGlobs" not in loaded["targets"][1]
        finally:
            os.unlink(csv_path)
            if os.path.exists(json_path):
                os.unlink(json_path)
