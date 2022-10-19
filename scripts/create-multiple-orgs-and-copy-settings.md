# Create multiple new orgs that all have the same settings in a given Group

## Description

Use this script to create multiple organizations in Snyk which their settings are copied from another, existing, organization.

For example, create an organization and change it's configuration to match your needs like enabling PR checks, integrations etc. Then crete multiple organization with our API and during their creation the settings will be copied from the template organization previously created.

## Flow and Endpoints

- Create a template organization in Snyk which will serve as template from which to copy the settings to the other organizations:
    - From the UI:
        - In your admin page, click on the org dropdown box (on the upper left) and click “Create a new organization”
            
        - Once the org is created, change its settings according to your needs (all these settings will eventually be copied to the new orgs), for example:
            - Add an integration
            - Configure the integration settings etc
    
    **OR**
    
- Use the create org API call and update settings:
    - [Create organization](https://snyk.docs.apiary.io/reference/organizations/create-organization/create-a-new-organization)
    - [View Organization Settings](https://snyk.docs.apiary.io/reference/organizations/organization-settings/view-organization-settings)
    - [Update Organization Settings](https://snyk.docs.apiary.io/reference/organizations/organization-settings/update-organization-settings)
    - [Integration cloning](https://snyk.docs.apiary.io/reference/integrations/integration-cloning/clone-an-integration-(with-settings-and-credentials))

- Run the create organization [API call](https://snyk.io/api/v1/org) (as many times as needed) and assign the reference organization as a source org, for example:
    - use this body:
        
        ```json
        {  
          "name": "new-org",
          "groupId": <YOUR_GROUP_ID>,
          "sourceOrgId": <TEMPLATE_ORG_ID>
        }
        ```
        

## Code examples

 (Typescript)
 ```tsx
    const fetch = require("node-fetch");
    const { isEqual } = require("lodash");
    
    const [token, groupPublicId, orgPublicId] = process.argv;
        
    const getNotifications = async (orgPublicId) => {
      return await fetch(
    	`https://api.snyk.io/v1/org/${orgPublicId}/notification-settings`,
    	{
      	headers: {
        	Authorization: `token ${token}`,
        	"Content-Type": "application/json",
      	},
    	}
      )
    	.then((res) =>
      	res.ok ? res : Promise.reject(new Error("Cannot get notifications"))
    	)
    	.then((res) => {
      	return res.json();
    	});
    };
    
    const copyOrg = async (sourceOrgId, groupId, name) => {
      return await fetch("https://api.snyk.io/v1/org", {
    	method: "post",
    	body: JSON.stringify({
      	name,
      	groupId,
      	sourceOrgId,
    	}),
    	headers: {
      	Authorization: `token ${token}`,
      	"Content-Type": "application/json",
    	},
      })
    	.then((res) =>
      	res.ok ? res : Promise.reject(new Error("Cannot copy org"))
    	)
    	.then((res) => {
      	return res.json();
    	});
    };
    
    const setNotifications = async (orgPublicId, notification) => {
      return await fetch(
    	`https://api.snyk.io/v1/org/${orgPublicId}/notification-settings`,
    	{
      	method: "put",
      	body: JSON.stringify(notification),
      	headers: {
        	Authorization: `token ${token}`,
        	"Content-Type": "application/json",
      	},
    	}
      )
    	.then((res) =>
      	res.ok ? res : Promise.reject(new Error("Cannot set notifications"))
    	)
    	.then((res) => {
      	return res.json();
    	});
    };
    
    const getAllOrgs = async (groupPublicId) => {
      return await fetch(
    	`https://api.snyk.io/v1/group/${groupPublicId}/orgs?perPage=1000`,
    	{
      	headers: {
        	Authorization: `token ${token}`,
        	"Content-Type": "application/json",
      	},
    	}
      )
    	.then((res) =>
      	res.ok ? res : Promise.reject(new Error("Cannot get all orgs"))
    	)
    	.then((res) => {
      	return res.json();
    	});
    };
    
    const deleteOrg = async (orgPublicId) => {
      return await fetch(`https://api.snyk.io/v1/org/${orgPublicId}`, {
    	method: "delete",
    	headers: {
      	Authorization: `token ${token}`,
      	"Content-Type": "application/json",
    	},
      })
    	.then((res) =>
      	res.ok ? res : Promise.reject(new Error("Cannot delete an org"))
    	)
    	.then((res) => {
      	return res.json();
    	});
    };
    
    const namePrefix = "main";
    
    const doTheThing = async (groupPublicId, orgPublicId) => {
      const notificationSettings = await getNotifications(orgPublicId);
    
      const existedOrgNames = await getAllOrgs(groupPublicId).then(({ orgs }) =>
    	orgs.map(({ name }) => name)
      );
    
      console.log(notificationSettings);
    
      for (let i = 1; i <= 100; i++) {
    	const orgName = `${namePrefix}-${i}`;
    
    	if (existedOrgNames.includes(orgName)) {
      	console.log("The org already existed", orgName);
      	continue;
    	}
    
    	const org = await copyOrg(orgPublicId, groupPublicId, orgName);
    	console.log("new org", org);
    
    	await setNotifications(org.id, notificationSettings);
    	console.log("set settings: OK");
    
    	const copyNotifications = await getNotifications(org.id);
    
    	if (!isEqual(copyNotifications, notificationSettings)) {
      	throw new Error("Notifications are set incorectly");
    	}
      }
    };
    
    doTheThing(groupPublicId, orgPublicId).then(() => {
      console.log("done!");
    });
    ```