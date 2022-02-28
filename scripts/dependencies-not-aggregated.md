# How to create a Report of License Dependencies not aggregated

## Description:
Customers are requesting license report not aggregated by licenses are we currently have on our UI.

## Proposed Solution
Use existing Dependencies API to get the data and build a new report, without aggregation.

This solution uses pysnyk (GitHub - snyk-labs/pysnyk: A Python client for the Snyk API. ) . Need to install it before using.

## Limitations
Copyright information is limited for npm and maven.

### Example of possible implementation
note: it is not looping the pagination. For real cases need to loop until all pages are read

```
from urllib2 import Request, urlopen
import json
import csv

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
      "languages": [
        "javascript",
        "ruby",
        "java",
        "dotnet"
      ],
      "projects": [],
      "dependencies": [],
      "licenses": [],
      "severity": [
        "high",
        "medium",
        "low"
      ],
      "depStatus": ""
    }
  }
"""

values = """
  {
    "filters": {
      "projects": ["YOUR-PROJECTS"]
    }
  }
"""
#be awere of pagination -> call in loop until no more pages
headers = {
  'Content-Type': 'application/json',
  'Authorization': 'YOUR-TOKEN'
}
request = Request('<https://snyk.io/api/v1/org/YOUR-ORG/dependencies?page=1&perPage=2000>', data=values, headers=headers)

response_body = urlopen(request).read()
#print response_body#
#dep = json.loads(response_body)
dep = json_loads_byteified(response_body)

ii = 0
with open('./dependencies.csv', mode='w') as dependecyFile:
  dependecyFile = csv.writer(dependecyFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
  dependecyFile.writerow( [ "Project ID" ,"Project Name" ,"License Id" , "License Title" , "License" , "Package Id", " Package Name", "Package Version" ,"Package Type","Copyrights"])
  for deps in dep['results']:
      #print (dep["results"][ii]['id']), "\\t"
      #print (dep['results'][ii]['id']) ,'\\t', (dep['results'][ii]['name']) ,'\\t', (dep['results'][ii]['version']) ,'\\t', (dep['results'][ii]['type']),'\\t'
      depId = (dep['results'][ii]['id'])
      depName = (dep['results'][ii]['name'])
      depVer = (dep['results'][ii]['version'])
      depType = (dep['results'][ii]['type'])
      iii=0
      for lics in dep['results'][ii]['licenses']:
        #print (dep['results'][ii]['licenses'][iii]['id']) , '\\t' ,dep['results'][ii]['licenses'][iii]['title'] ,'\\t' , dep['results'][ii]['licenses'][iii]['license']
        licId = (dep['results'][ii]['licenses'][iii]['id'])
        licTitle = dep['results'][ii]['licenses'][iii]['title']
        licLicense = dep['results'][ii]['licenses'][iii]['license']
        iii=iii+1
      copy=""
      if 'copyright' in dep['results'][ii]:
        #print (dep['results'][ii]['copyright'])
        copy =  (dep['results'][ii]['copyright'])
          #reset iii for loop on projs
      iii=0
      for projs in dep['results'][ii]['projects']:
        #print (dep['results'][ii]['projects'][iii]['id']) , '\\t' ,dep['results'][ii]['projects'][iii]['name'] ,'\\t'
        projID = (dep['results'][ii]['projects'][iii]['id'])
        projName = dep['results'][ii]['projects'][iii]['name']
        iii=iii+1
        #print projID , "t" , projName, "\\t" , licId , "\\t", licTitle , "\\t", licLicense , "\\t" , depName, "\\t", depVer , "\\t", copy
        dependecyFile.writerow( [ projID ,projName,licId , licTitle , licLicense , depId, depName, depVer ,depType,copy])
      ii= ii+1
```
