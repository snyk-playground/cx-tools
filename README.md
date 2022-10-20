![snyk-oss-category](https://github.com/snyk-labs/oss-images/blob/main/oss-example.jpg)

<br/>
<div align="center">
This is a list of examples and scripts compiled by the Snyk Customer Experience teams for the purpose of solving specific use cases raised by customers.
</div>
<br/>


# Scripts
- ["Remediation Advice" for Snyk Container](scripts/Remediation-container.md)
- [Dependencies by project CSV](scripts/dependencies-csv.md)
- [Fixed Issues by Org CSV](scripts/fixed-issues-by-org.md)
- [How can customer pull list of all repos imported to Snyk?](scripts/get-gh-repos.md)
- [How to add user to same orgs as other user](scripts/add-user.md)
- [How to add conditions for blocking PR when a new vuln is found? (How to filter data from snyk-delta)](scripts/block-pr-delta.md)
- [How to Copy ignore from one project to another](scripts/copy-ignore.md)
- [How to create a Report of License Dependencies not aggregated](scripts/dependencies-not-aggregated.md)
- [How to delete all projects of a repo](scripts/delete-projects-from-repo.md)
- [How to Get Last Project Monitor](scripts/get-last-proj-monitor.md)
- [How to Import all Project with suffix](scripts/import-proj-with-sufix.md)
- [How to Keep Projects History snapshots](scripts/keep-proj-history.md)
- [How to Save Ignored vulns as .snyk file](scripts/ignores-to-policy-file.md)
- [How to Scan All Projects by File Type](scripts/scan-proj-from-type.md)
- [How to Scan all unmanaged JARs](scripts/scan-all-unmanaged-jars.md)
- [How to Send new ignores to Slack](scripts/new-ignores-slack.md)
- [How to Silence snyk exit code and create advanced conditions to fail the build](scripts/silence-exit-code.md)
- [How to Understand if vulnerability was added by developer or is a new vulnerability discovered](scripts/vul-added-or-discovered.md)
- [How to use the Snyk API to find and remove all empty targets from a Snyk group](rm-empty-targets)
- [How to count the targets in a Snyk group (by integration type)](target-counter)
- [How to check for "stale" projects -- not tested since a specific date](projects-not-tested-since)
- [How to disable all notifications for a user](snyk-quiet)
- [How to assign users to all orgs](scripts/assign-users-to-all-orgs.md)
- [How to rotate snyk broker token](scripts/broker-token-rotation.md)
- [How to bulk ignore issues](scripts/bulk-ignore-issues.md)
- [How to create multiple orgs and copy settings fron an existing org](scripts/create-multiple-orgs-and-copy-settings.md)
- [How to detect and import new projects](scripts/detect-and-import-new-projects.md)
- [How to disable all interaction fron snyk for a while](scripts/disable-all-interaction-from-snyk.md)
- [How to find all snyk projects impacted by a certain vuln](scripts/find-all-projects-affected-by-a-vuln.md)
- [How to identify and import new repos](scripts/Identify-and-import-new-repos.md)
- [How to find import new container images](scripts/import-new-container-images.md)
- [How to list all issues for a snyk org](scripts/list-all-issues-for-a-snyk-org.md)
- [How to get projects snapshots](scripts/retrieve-projects-snapshots.md)
- [How to tag snyk projects](scripts/tag-snyk-projects.md)
- [How to generate a list (CSV) of all user and service accounts in a group](userlist)
- [Pysnyk examples](https://github.com/snyk-labs/pysnyk/tree/master/examples)

# Guides
In the folder [webhook-examples](./webhook-examples/README.md) we provide some guides on how to use Snyk webhooks to forward Snyk vulnerability data to other systems. These examples include the following:
- <img src="./webhook-examples/azure-devops-boards-logo.png" width="50"> [Azure DevOps Boards](./webhook-examples/azure-function-azure-boards.cs)
- <img src="./webhook-examples/microsoft-teams-logo.png" width="50"> [Microsoft Teams](./webhook-examples/azure-function-microsoft-teams.cs)
- <img src="./webhook-examples/newrelic-logo.png" width="50"> [New Relic Events](./webhook-examples/azure-function-newrelic.cs)
- <img src="./webhook-examples/datadog-logo.png" width="50"> [DataDog](./webhook-examples/azure-function-datadog.cs)
- <img src="./webhook-examples/slack-logo.png" width="50"> [Slack](https://docs.snyk.io/snyk-api-info/snyk-webhooks/using-snyk-webhooks-to-connect-snyk-to-slack-with-aws-lambda)
- <img src="./webhook-examples/splunk-logo.png" width="50"> [Splunk Observability Cloud](./webhook-examples/azure-function-splunk.cs)
- <img src="./webhook-examples/splunk-logo.png" width="50"> [Splunk Cloud HTTP-Event-Collector (HEC)](./Snyk-to-Splunk-HTTP-Event-Collector/)

# Customers Shared Scripts
- [Citrix - BitBucket sync to Snyk](BB-to-snyk/bitbucketToSnyk-share.py)
- [MessageMedia - Export BitBucket projects to JSON format](create-snyk-json/create-snyk-import-json/py)
- [Avishai - A package that wraps pysnyk library for easier usage from cli interfaces](https://github.com/avishayil/python-snyk-test)
- [Lunar - Prometheus exporter for Snyk ](https://snyk.io/blog/vulnerability-monitoring-with-snyk-prometheus-and-grafana/)(https://github.com/lunarway/snyk_exporter)

# Snyk repos and tools
- [A curated list of awesome Snyk community contributions](https://github.com/snyk/awesome-snyk-community)
- [Snyk Technical Services](https://github.com/snyk-tech-services)
- [Snyk Labs (user sync, etc)](https://github.com/snyk-labs)
- [A Python client for the Snyk API](https://github.com/snyk-labs/pysnyk)
- [Snyk to SPDX](https://www.npmjs.com/package/snyk2spdx) : details [here](https://snyk.io/blog/advancing-sbom-standards-snyk-spdx/)
