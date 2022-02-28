# How to add conditions for blocking PR when a new vuln is found (filter data from snyk-delta)

## Example 1: Customer does not want to block a PR when the newly added vulnerability does not have a fix.

### Instructions
Run the following jq instructions to delete the vulnerabilities without fix from the JSON used for snyk delata

```
snyk test --json --print-deps  | jq 'del(.vulnerabilities[]? |  select(.fixedIn == []))' | snyk-delta
```

## Example 2: Customer does not want to block a PR when the newly added vulnerability is of license type.

### Instructions
Run the following jq instructions to delete the issues with type = null from the JSON used for snyk delata

```
snyk test --json --print-deps | jq 'del(.vulnerabilities[]? | select(.type != null))' | snyk-delta
```
