# GitHub merge queues with Snyk required checks

**Solution note — GitHub Actions workaround for merge queue status checks**

| | |
|---|---|
| **Audience** | Teams using **GitHub merge queues** and **Snyk** with **required status checks** on protected branches |
| **Scope** | Supplies a passing check **name** on `merge_group`; does **not** replace Snyk scanning on pull requests |
| **Artifact** | [`.github/workflows/snyk-merge-queue-bypass.yml`](.github/workflows/snyk-merge-queue-bypass.yml) |

---

## Overview

Snyk’s native GitHub integration does not report status checks on **merge queue** (`merge_group`) runs. If branch protection requires a Snyk check by name, the merge queue can stall because that check never appears for the merge-group commit.

This repository provides a **GitHub Actions workflow** that implements the **merge-queue bypass pattern** Snyk describes when native PR checks cannot run on `merge_group`: on merge queue, it publishes a **successful** GitHub check whose **name exactly matches** your required Snyk check, so merge queues can complete. **It does not run Snyk**; you still rely on Snyk results from the pull request (native PR checks and/or CI on `pull_request`). For general PR check behavior, see [Snyk’s pull request checks documentation](https://docs.snyk.io/scan-with-snyk/pull-requests/pull-request-checks/configure-pull-request-checks).

## What you keep

- **Snyk native PR checks** can stay enabled. They continue to run on normal pull requests as they do today.
- The workflow only runs on **merge queue** events and fills the missing status **name** for that path.

## Setup

### 1. Add the workflow to your repo

Copy [`.github/workflows/snyk-merge-queue-bypass.yml`](.github/workflows/snyk-merge-queue-bypass.yml) into the **default branch** (and any protected branch that uses a merge queue) so GitHub can run it when a merge group is built.

### 2. Configure the check name

The workflow uses the GitHub Checks API so the status name matches Snyk’s app check **character for character** (a plain Actions job name often does not, because GitHub labels jobs as `Workflow name / Job name`).

1. In GitHub: **Settings** → **Branches** → your protected branch → **Required status checks**.
2. Find the Snyk line (for example `code/snyk (your-org)`) and copy it **exactly**.
3. **Settings** → **Secrets and variables** → **Actions** → **Variables** → **New repository variable**:
   - **Name:** `SNYK_REQUIRED_CHECK_NAME`
   - **Value:** that exact string.

For the same name at the organization level, create an organization variable with the same name (repository variables override organization variables when both exist; use whichever matches your standards).

### 3. Branch protection

- Require the **same** status check name as in step 2.
- Per Snyk’s guidance, **do not** restrict that required check to only the Snyk GitHub App as its source. The merge-queue run is satisfied by a check created by **GitHub Actions**; the rule must allow that source (typically “any” / name-only).

### 4. Optional: limit which branches use the workflow

If only certain branches use a merge queue, open the workflow file and uncomment the `branches:` list under `merge_group`.

## Security and process

The merge-queue check is a **placeholder** so automation can proceed. Your real security gate should remain **Snyk (and review) on the pull request** before code enters the queue. The workflow’s check output states this for anyone reviewing check details or audits.

## Files

| Item | Purpose |
|------|---------|
| `.github/workflows/snyk-merge-queue-bypass.yml` | Runs on `merge_group`, creates a successful check named `SNYK_REQUIRED_CHECK_NAME` |

For implementation notes (why the Checks API is used, and a commented “simple job” alternative), see the comments at the top of the workflow file.

---

## Support

| Resource | Link |
|----------|------|
| Configure Snyk pull request checks | [docs.snyk.io — Configure pull request checks](https://docs.snyk.io/scan-with-snyk/pull-requests/pull-request-checks/configure-pull-request-checks) |
| Troubleshoot PR checks | [docs.snyk.io — Troubleshoot PR checks](https://docs.snyk.io/scan-with-snyk/pull-requests/pull-request-checks/troubleshoot-pr-checks) |
| GitHub merge queues | [docs.github.com — Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) |
| Snyk Support | [support.snyk.io](https://support.snyk.io) |

This document describes a common integration pattern for GitHub merge queues and Snyk. It is not a substitute for [Snyk Support](https://support.snyk.io) or your account team when you need guidance specific to your organization, contract, or GitHub Enterprise settings.
