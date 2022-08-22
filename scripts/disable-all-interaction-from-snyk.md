# Disable all PRs / Tests & any interactions Snyk might have with my SCM for a certain event/time

## User need

Use this script to disable all interaction from Snyk to my SCM for a given time period

## Flow and Endpoints

### Flows

### Approach # 1

### Webhooks Approach

- Remove the Snyk webhook by getting the Webhook Id and using it to delete the webhook

### Approach # 2

- Get integrations from different organizations and then update each integrations settings.

1. [Get all integrations first](https://snyk.docs.apiary.io/#reference/integrations/list)
2. [Go through each integration to get the integration settings by integration ID](https://snyk.docs.apiary.io/#reference/integrations/integration-settings/retrieve)
3. Return integration IDs into an array along with associated settings.
4. Update integration settings to off. Looped through each integration setting data attribute and set it to false. Focus on making sure all SCM settings are identified and set to off.
5. Later down the line turn the settings back on.

## Endpoints used

**Approach #1**

*Webhooks Approach:*

- [Get all webhooks per org](https://snyk.docs.apiary.io/#reference/webhooks/webhook-collection/list-webhooks)
- [Delete the desired webhook](https://snyk.docs.apiary.io/#reference/webhooks/webhook/delete-a-webhook)
- [Reinstate the webhook afterwards](https://snyk.docs.apiary.io/#reference/webhooks/webhook-collection/create-a-webhook)

*Approach #2*

- [Get a list of all integrations](https://snyk.docs.apiary.io/#reference/integrations/integrations/list)
- [Get integration settings](https://snyk.io/api/v1/org/orgId/integrations/integrationId/settings)
- [Update integration settings](https://snyk.docs.apiary.io/#reference/integrations/integration/update-existing-integration) - This will be done twice: once to turn things "off" and then back "on"