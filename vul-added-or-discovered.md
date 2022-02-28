# How to Understand if vulnerability was added by developer or is a new vulnerability discovered

## Description:
Customers are looking for a way to determine through the API whether a vulnerability has been recently introduced by a development team (e.g. consequence of a change in the dependency graph) or it has been recently discovered (e.g. consequence of a vuln being added to the Snyk Vuln DB).

## Proposed Solution
Use the Reporting Issue API (Snyk API · Apiary ), you will get these parameters: “introducedDate” and “disclosureTime”.

Comparing both you will be able to understand if a vuln was introduced by a developer or not ( "introducedDate” > “disclosureTime”)

## Example of possible implementation
### Option 1 - With python code

```
#this runs only in pyhon 2 (python 3 needs to replace urllib2)
#run only for vulns, not license. -> Licenses does not have disclosure date

from urllib2 import Request, urlopen
import json
def json_load_byteified(file_handle):
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )

def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )

#function to get string without unicode u prefix
def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data

values = """
  {
    "filters": {
      "orgs": [
        "YOUR_ORG"
      ],
      "severity": [
        "high",
        "medium",
        "low"
      ],
      "exploitMaturity": [
        "mature",
        "proof-of-concept",
        "no-known-exploit",
        "no-data"
      ],
      "types": [
        "vuln"
      ],
      "languages": [
        "javascript",
        "ruby",
        "java",
        "scala",
        "python",
        "golang",
        "php",
        "dotnet"
      ],
      "projects": [
        "YOUR_RPOJECT"
      ],
      "issues": [],
      "identifier": "",
      "ignored": false,
      "patched": false,
      "fixable": false,
      "isFixed": false,
      "isUpgradable": false,
      "isPatchable": false,
      "isPinnable": false
    }
  }
"""

headers = {
  'Content-Type': 'application/json',
  'Authorization': 'YOUR-TOKEN'
}
request = Request('<https://snyk.io/api/v1/reporting/issues/?from=2020-01-01&to=2020-07-07>', data=values, headers=headers)

response_body = urlopen(request).read()

#vulns = json.loads(response_body)
vulns = json_loads_byteified(response_body)

ii = 0
for vul in vulns['results']:
    print (vulns["results"][ii]['issue']['id']) ,"disclosure: ", (vulns["results"][ii]['issue']['disclosureTime']), " introduced : " ,(vulns["results"][ii]['introducedDate'])

    ii= ii+1
```

### Option 2 - Script:

```
#curl -s \\
#     --header "Content-Type: application/json" \\
#     --header "Authorization: 7db595c1-675a-4394-83fc-a182b76c38d5" \\
#  '<https://snyk.io/api/v1/org/3842b754-f9b0-4500-b6da-3c21bb8c3f47/projects>' | jq  '.projects'

curl -s \\
     --request POST \\
     --header "Content-Type: application/json" \\
     --header "Authorization: YOUR-TOKEN" \\
     --data-binary "{
  \\"filters\\": {
    \\"orgs\\": [\\"YOUR-ORG\\"],
    \\"severity\\": [
      \\"high\\",
      \\"medium\\",
      \\"low\\"
    ],
    \\"exploitMaturity\\": [
      \\"mature\\",
      \\"proof-of-concept\\",
      \\"no-known-exploit\\",
      \\"no-data\\"
    ],
    \\"types\\": [
      \\"vuln\\"
    ],
    \\"languages\\": [
      \\"javascript\\",
      \\"ruby\\",
      \\"java\\",
      \\"scala\\",
      \\"python\\",
      \\"golang\\",
      \\"php\\",
      \\"dotnet\\"
    ],
    \\"projects\\": [\\"YOUR-PROJECT\\"],
    \\"issues\\": [],
    \\"identifier\\": \\"\\",
    \\"ignored\\": false,
    \\"patched\\": false,
    \\"fixable\\": false,
    \\"isFixed\\": false,
    \\"isUpgradable\\": false,
    \\"isPatchable\\": false,
    \\"isPinnable\\": false
  }
}" \\
'<https://snyk.io/api/v1/reporting/issues/?from=2020-01-01&to=2020-07-07>' | jq  ' .results[].issue.id, .results[].issue.disclosureTime, .results[].introducedDate'
```
