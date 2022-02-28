# Description
Output number of fixed issues by severity for each org for a given token scope and timeframe (start and end date)

## Instructions
https://gist.github.com/scotte-snyk/36a4ac8546b05b6110cc4b05525fe1cf

## Usage
SNYK_TOKEN must be set in your environment

```
./fixed_issues_by_org.py [options] [start_date] [end_date]
        options:
           -d
           enable debug mode
           -j
           output results in JSON format

        start_date
           -s <start-date>
        end_date
           -e <end-date>

      examples:
        ./fixed_issues_by_org.py -j -s 2021-04-21 -e 2021-04-22
```

## example: generate CSV

```
./fixed_issues_by_org.py -s 2021-04-10 -e 2021-04-24 > results.csv
```

## example: generate JSON result

```
./fixed_issues_by_org.py -j -s 2021-04-10 -e 2021-04-24 > results.json
```
