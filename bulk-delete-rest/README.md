<h2>What is this tool for? </h2> <br>

This tool allows you to delete projects in bulk within Snyk by specifying a set of organazations and types of projects to delete<br>

<h2>Installation instructions</h2><br>

Clone this repo and run <pre><code>pip install -r requirements.txt</pre></code><br>

<h2>How do I use this tool? </h2><br>

Set your snyk token with <pre><code>export SNYK_TOKEN=TOKEN-GOES-HERE</code></pre><br>

Within the cloned repo run <pre><code>python3 snyk-bulk-delete.py (add flags here)</code></pre><br> add the necessary flags listed below <br>

PROJECTS ARE DE-ACTIVATED BY DEFAULT AND NO ACTIONS ARE APPLIED UNLESS --FORCE FLAG IS USED, SEE DETAILS BELOW<br>
<pre><code>
  -h, --help                    show this help message and exit
  --orgs ORGS                   A set of org slugs upon which to perform operations (use ! for all orgs).
  --region REGION               Snyk API region (e.g., 'eu', 'au', 'us-02'). Leave empty for default (US-01 global).
  --origins ORIGINS             Defines origin/source_types of projects/targets to delete (e.g., github, cli).
  --ignore-keys IGNORE_KEYS     If any of these keys are present in a project/target name, it will not be targeted.
  --targets                     [Mode] Query and delete Targets directly instead of Projects.
  --sca-types SCA_TYPES         [Project Mode Only] Defines SCA type/s to delete.
  --products PRODUCTS           [Project Mode Only] Defines product/s types to delete (opensource, container, iac, or sast).
  --after AFTER                 [Project Mode Only] Delete projects created after date time (ISO 8601).
  --before BEFORE               [Project Mode Only] Delete projects created before date time (ISO 8601).
  --delete                      [Project Mode Only] Delete active projects instead of deactivating them.
  --delete-non-active-projects  [Project Mode Only] Delete non-active projects instead of deactivating.
  --delete-empty-orgs           Delete all orgs that do not have any remaining projects.
  --force                       Apply actions (script runs as dry run by default).
 * Please replace spaces with dashes(-) when entering orgs <br>
 * If entering multiple values use the following format: "value-1 value-2 value-3"<br>
 * Types and origins are defined under this API > https://snyk.docs.apiary.io/#reference/projects/individual-project/retrieve-a-single-project
</code></pre>

Example where all opensource npm and gradle projects from github are deleted within test-org-1 and test-org-2
<br>
<pre><code>python3 snyk-bulk-delete.py --orgs "test-org-1 test-org-2" --products opensource --sca-types "npm gradle" --origins github
</code></pre>



