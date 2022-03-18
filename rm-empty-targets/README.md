# rm-empty-targets.py

This script is an example of how to use the Snyk API to find and
remove all empty targets from a Snyk group. It uses pysnyk to
make a list of the orgs in the group, and then makes use of the
following APIs to enumerate and delete the targets:

[Get targets by org ID](https://apidocs.snyk.io/?version=2022-03-01%7Eexperimental#get-/orgs/-org_id-/targets)
[Delete target by target ID](https://apidocs.snyk.io/?version=2022-03-01%7Eexperimental#delete-/orgs/-org_id-/targets/-target_id-)

The algorithm used by this example is as follows:

```
- Get list of orgs
- For each org:
    - get all the targets for the org
    - get all the non-empty targets for the org (use the "excludeEmpty" filter)
    - find the empty targets by comparing the non-empty list with the complete list and using the difference
    - add the empty targets to a dictionary of targets keyed by organization ID
- Iterate through the dictionary of empty targets and delete each one
```

The script outputs a list of the org/targets that were deleted (or
would have been deleted, if using `--dry-run`) to `stdout`, one per line.
