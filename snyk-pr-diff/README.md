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
- GitHub Action examples:
    Code: https://github.com/snyk-playground/cx-tools/blob/main/snyk-pr-diff/examples/github-action-snyk-code-diff.yml
    IaC:  https://github.com/snyk-playground/cx-tools/blob/main/snyk-pr-diff/examples/github-action-snyk-iac-diff.yml

## GitHub Action Screenshot
![image](https://github.com/hezro/snyk-code-pr-diff/assets/17459977/e90671d3-bfa1-413e-b85a-fba642008c1b)


