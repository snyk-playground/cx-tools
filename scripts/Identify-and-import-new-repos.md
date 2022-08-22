# Identify and import new repos only

## Description

Use this script to find newly added repos and import them into Snyk

## Flow and Endpoints

- List all SCM repos - The API call for that changes according to the SCM (Github, Bitbicket, Azure etc)
- [List of Snyk Targets for this org](https://apidocs.snyk.io/?version=2022-07-08%7Ebeta#get-/orgs/-org_id-/targets)
- Processing engine to delta those lists
- Import engine to drive importing the gaps between them using the [import API call](https://snyk.docs.apiary.io/#reference/import-projects/import-targets)
- Automating the solution

## Code examples (For Github Enterprise)

(Javascript)

```tsx
const { Octokit } = require("@octokit/rest");
const fs = require("fs");

const needle = require("needle");

const gheToken = process.env.GHE_TOKEN_FOR_API_CALLS;
const snykToken = process.env.SNYK_TOKEN_FOR_API_CALLS;

async function run() {
  try {
    const snykTargets = new Set(await getSnykTargets());
    const gheRepos = new Set(await getGheRepos());

    const reposToImport = difference(gheRepos, snykTargets);

    await importRepos([...reposToImport]);
  } catch (err) {
    console.error(err);
    console.error("Failed");
    process.exit(1);
  }
}

async function getGheRepos() {
  const octokit = new Octokit({
    auth: gheToken,
    baseUrl: "https://ghe.dev.snyk.io/api/v3",
  });

  const { data: repos } = await octokit.rest.repos.listForOrg({
    org: ${GHE_ORG_NAME},
  });

  return repos.map((r) => r.full_name);
}

function difference(setA, setB) {
  let _difference = new Set(setA);
  for (let elem of setB) {
    _difference.delete(elem);
  }
  return _difference;
}

async function getSnykTargets() {
  // TODO USE PAGINATION?

  return new Promise((resolve, reject) => {
    const url =
      "https://api.snyk.io/v3/orgs/${SNYK_ORG_ID}/targets?version=2022-07-08~beta";

    const options = {
      headers: {
        Authorization: `token ${snykToken}`,
      },
    };

    needle.get(url, options, (err, res) => {
      if (err) {
        reject(err);
        return;
      }

      const snykTargets = res.body.data.map((t) => t.attributes.displayName);
      resolve(snykTargets);
    });
  });
}

async function importRepos(repos) {
  return new Promise(async (resolve, reject) => {
    const endpoint =
      "https://snyk.io/api/v1/org/${SNYK_ORG_ID}/integrations/${SNYK_ORG_INTEGRATION_ID}/import";

    const targets = repos.map((r) => {
      const [owner, name] = r.split("/");
      return {
        target: { owner, name, branch: "master" /* TODO get default branch */ },
      };
    });

    for (const t of targets) {
      const importCall = new Promise((resolve, reject) => {
        console.log(JSON.stringify(t, null, 4));

        const options = {
          headers: {
            Authorization: `token ${snykToken}`,
          },
        };

        needle.post(endpoint, t, options, (err, res) => {
          console.log(res.body);
          err ? reject(err) : resolve();
        });
      });

      try {
        const r = await importCall;
        console.log(r);
      } catch (err) {
        reject(err);
        return;
      }
    }

    resolve();
  });
}

run()
  .then(() => console.log("Done"))
  .catch(console.error);
```