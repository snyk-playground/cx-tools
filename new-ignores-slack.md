# How to Send new ignores to Slack

## Description
This script is meant to take all of the ignores for Snyk and create a baseline and send these notifications to Snyk. One this is done, the customer can run a cron job to run the script which will read from a file and send slack message to a channel for new ignores.

## The script

```
import argparse
import re
import urllib3
import requests
import json

from snyk import SnykClient
from utils import get_token, get_default_token_path


def parse_command_line_args():
    parser = argparse.ArgumentParser(description="Snyk API Examples")
    parser.add_argument("--targetFile", type=str,
                        help="File that stores previous ignores", required=True)
    parser.add_argument("--slackWebhookURL", type=str,
                        help="Slack webhook URL to send messages", required=True)
    args = parser.parse_args()
    return args


snyk_token_path = get_default_token_path()
snyk_token = get_token(snyk_token_path)
args = parse_command_line_args()
targetFile = args.targetFile
slackWebhook = args.slackWebhookURL

client = SnykClient(token=snyk_token)
http = urllib3.PoolManager()

orgsList = []
ignoreList = []
previousIgnores = []

# List of all organizations for user/service account
allOrgs = client.organizations.all()
print('Collecting organization IDs of user or service account...')
# extacts org IDs
for f in allOrgs:
    orgId = (re.findall('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',repr(f)))
    orgsList.append(orgId[0])


print ('Collecting ignores in your organizations...this may take a few minutes')
# Collect ignores
for i in orgsList:
    for proj in client.organizations.get(i).projects.all():
        projId = (re.findall('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',repr(proj)))
        url = "org/" + i + "/project/" + projId[2] + "/ignores"
        try:
            r = client.get(url)
            parsed_input = r.json()
            if parsed_input:
                ignoreList.append(parsed_input)
                print (parsed_input)
        except Exception as e:
            if e == '<Response [404]>':
                print('Error gathering ignores for the following organization ' + parsed_input)

ignoreCount = len(ignoreList)
orgCount = len(orgsList)

print ('There are ' + str(ignoreCount) + ' ignores across ' + str(orgCount) + ' organizations.')

# Checking if file is empty and writing previous ignores to a list
print('Opening file...')
with open(targetFile, 'r') as f:
    fileIgnore = f.read().splitlines()
    # Remove duplicates
    fileIgnores = set(fileIgnore)
    # for i in fileIgnores:
    #     print (i)
    if len(fileIgnores) == 0:
        print ("File is empty.")
        # Updating list with new ignores
        print ('Sending new ignores to slack channel...')
        for ignore in ignoreList:
            print ("Sending Slack message" + str(ignore))
            name = re.findall(r'\w[^\']*', str(ignore))
            slack_msg = {'text': 'New ignore from Snyk: ' + str(name[0])}
            requests.post(slackWebhook, data=json.dumps(slack_msg))
            previousIgnores.append(ignore)
    else:
        for ignoreFile in fileIgnores:
            print (ignoreFile)
            previousIgnores.append(ignoreFile)
            print ('Comparing previous ignores with collected ignores...')
            # Comparing ignores to old ignores
        for ignore in ignoreList:
            notFound = False
            for x in fileIgnores:
                currentIgnore = re.findall(r'\w[^\']*', str(ignore))
                pastIgnore = re.findall(r'\w[^\']*', str(x))
                if len(currentIgnore) > 0:
                    current = ""
                    current = currentIgnore[0]
                    current = current.strip()
                    print (current)
                else:
                    current = ""
                    current = currentIgnore
                    current = current.strip()
                if len(pastIgnore) > 0:
                    past = ""
                    past = pastIgnore[0]
                    past = past.strip()
                else:
                    past = ""
                    past = pastIgnore
                    past = past.strip()
                if current == past:
                    print ("Previously ignored " + str(current))
                    break
                else:
                    notFound = True
            if notFound:
                print ("Not Found.  Sending Slack message " + str(current) + " past ignore: " + str(past))
                name = re.findall(r'\w[^\']*', str(ignore))
                slack_msg = {'text': 'New ignore from Snyk: ' + str(name[0])}
                requests.post(slackWebhook, data=json.dumps(slack_msg))
                previousIgnores.append(ignore)

for e in fileIgnores:
    previousIgnores.append(e)

# Writing ignores to file
print ("Updating ignore list file with new ignores...")
with open(targetFile, 'w') as newFile:
    for row in previousIgnores:
        newFile.write("%s\n" % row)
```

### How to run it:
First, you’ll need to install the pysnyk dependency here link to the Pysnyk repo: https://github.com/snyk-labs/pysnyk

Using the client requires you to provide your Snyk API token.
```
import snyk

client = snyk.SnykClient("<your-api-token>")
```

### Arguments:
To use the script you’ll need to create a .txt file and specify the location with the --targetFile when you run the script. This is required.

The next argument that you’ll need to specify is the --slackWebhookURL and you can find instructions on how to create this webhook here

https://api.slack.com/messaging/webhooks#enable_webhooks

### Running the script:
When you specify a service account, make sure that it has group level access to collect the ignores for all of your organizations. Once you do that, you’ll need to run the script with a python 2.7 or higher and it’ll look like this: python3.7 http://api-demo-12-move-projects.py/

```
--targetFile=/Users/roberthicks/Desktop/test/snykigoretoslack/data.txt --slackWebhookURL=https://hooks.slack.com/services/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
```


### !!!Caveat!!!
Currently, the script is having issues with duplicate ignores. It will notify you every time if you ignored the same vulnerability twice.
