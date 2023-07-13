# Snyk PR Diff

Fail Snyk CLI scans only if there are new issues introduced (similar to automated Snyk PR checks).
Gets the delta between two Snyk Code or IaC JSON files before failing the scan. Particularly useful when running [Snyk CLI](https://github.com/snyk/cli) scans in your local environment, git hooks, CI/CD etc.


Compares two JSON files for both Snyk Code and IaC to provide details on:
- New vulnerabilities not found in the baseline scan

## Prerequisites
- Must provide two Snyk Code or IaC JSON files: one baseline scan and one scan where code changes have occurred


## Supported Snyk products

| Product | Supported |
| ---- | --------- |
| Code   | ✅     |
| Open Source    | ❌        |
| Container   | ❌        |
| IaC   | ✅         |

## Usage
- Run a Snyk scan and output a JSON file as the baseline.
- Run another Snyk scan that has code changes and output a JSON file.
- Usage: `snyk-pr-diff` `<code/iac>` `<baseline_scan.json>` `<pr_scan.json>`
- Example: ```snyk-diff-amd64-linux code /home/runner/work/goof/goof/snyk_code_baseline.json /home/runner/work/goof/goof/snyk_code_pr.json ```
  

## Examples
GitHub Action examples:
- Code: https://github.com/snyk-playground/cx-tools/blob/main/snyk-pr-diff/examples/github-action-snyk-code-diff.yml
- IaC:  https://github.com/snyk-playground/cx-tools/blob/main/snyk-pr-diff/examples/github-action-snyk-iac-diff.yml

## GitHub Action Screenshot
Code Output:

![image](https://github.com/snyk-playground/cx-tools/assets/20120261/d1a134f8-0393-4524-8095-7ed92c8e9c0d)

IaC Output:

![image](https://github.com/snyk-playground/cx-tools/assets/20120261/c3b846ff-9eae-403a-886d-bd180f92b4f9)




