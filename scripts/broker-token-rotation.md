# Broker at scale

## User need

Use this method to rotate/change your broker token for any reason

## Flow and Endpoints

### Flow

1. Self-enable broker via API
2. Retrieve broker client token
3. Enable Snyk broker permissions in Github Enterprise
4. Setup orgs
5. Set up integrations for each orgs
6. [Set up brokers](https://docs.snyk.io/features/snyk-broker/set-up-snyk-broker)
7. Import projects
8. Figure out when to rotate the token – use rotation & switching API endpoints
    1. [Provision a new broker token](https://snyk.docs.apiary.io/#reference/integrations/integration-broker-token-provisioning/provision-new-broker-token)
    2. [Switch to the new broker token](https://snyk.docs.apiary.io/#reference/integrations/integration-broker-token-switching/switch-between-broker-tokens)
    3. Re-test a project successfully and see logs in the new broker coming through

### Endpoints used:

1. [Get all org IDs (only group admin)](https://snyk.docs.apiary.io/#reference/organizations/the-snyk-organization-for-a-request/list-all-the-organizations-a-user-belongs-to)
2. [Add new integration](https://snyk.docs.apiary.io/#reference/integrations/integrations/add-new-integration)
3. [Update integration to enable broker](https://snyk.docs.apiary.io/#reference/integrations/integration/update-existing-integration)
4. Repeat for all other orgs & get broker token for each

### Token Rotation tasks:

1. [Broker provisioning API](https://snyk.docs.apiary.io/#reference/integrations/integration-broker-token-provisioning/provision-new-broker-token)
2. [Broker token switching](https://snyk.docs.apiary.io/#reference/integrations/integration-broker-token-switching/switch-between-broker-tokens)
    1. Note: needs admin permissions
