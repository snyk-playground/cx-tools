import json
import os

import jsoncomparison
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from apis.pagination import next_page
from apis.rest_api import groups, group_orgs
from apis.snyk_api import org_integrations, get_org_integration_settings, update_org_integration_settings

CFG_DELIMITER = "::"
width, height = A4
y = height - 2 * cm

# Handle pagination
# Is the current org in scope?
def org_of_interest(orgs, orgname):
    if orgs == None or orgname in orgs:
        return True
    return False


# Parse all the integrations for a group/specific orgs of interest to a file
def parse_integrations(args):
    orgs_integrations = dict()
    g_response = None

    try:
        g_pagination = None
        while True:
            # Retrieve all my groups
            g_response = json.loads(groups(g_pagination).text)

            go_response = None
            try:
                # Iterate to the named group
                for group in g_response['data']:
                    if group['attributes']['name'] == args['grp_name']:
                        go_pagination = None
                        while True:
                            go_response = json.loads(group_orgs(group, go_pagination).text)

                            # Iterate to the named Org
                            for org in go_response['data']:
                                if org_of_interest(args["org_names"], org['attributes']['name']):

                                    # Parse the integrations
                                    org_ints_response = json.loads(org_integrations(org['id']).text)
                                    orgs_integrations[org["attributes"]["name"] + CFG_DELIMITER + org["id"]] = {}

                                    # Collate the integration settings by name within the org
                                    for org_int in org_ints_response:
                                        settings = json.loads(get_org_integration_settings(org['id'], org_ints_response[org_int]).text)
                                        orgs_integrations[org['attributes']['name'] + CFG_DELIMITER + org["id"]] \
                                            [org_int + CFG_DELIMITER + org_ints_response[org_int]] = settings

                            # Next page?
                            go_pagination = next_page(go_response)
                            if go_pagination is None:
                                break

            except UnboundLocalError as err:
                print(err)
                print("GET call to /orgs API returned no 'data'")
                print(json.dumps(go_response, indent=4))
            except TypeError as err:
                print(err)

            # Next page?
            g_pagination = next_page(g_response)
            if g_pagination is None:
                break
    except UnboundLocalError as err:
        print(err)
        print("GET call to /groups API returned no 'data'")
        print(json.dumps(g_response, indent=4))
    finally:
        return orgs_integrations


# Update the integrations with the config persisted in a file
def update_integrations(args):
    try:
        my_config = args["config"]
        orgs = load_json_file(my_config)
        print(f"Organisation data parsed from {my_config}")
        template = None

        if args["template"] is not None:
            template = load_json_file(args["template"])
            my_config = args["template"]

        for org in orgs:
            org_name = org.split(CFG_DELIMITER)[0]
            org_id = org.split(CFG_DELIMITER)[1]

            # Iterate over the orgs, identify the config data and apply it
            for integration in orgs[org]:
                try:
                    integration_name = integration.split(CFG_DELIMITER)[0]
                    integration_id = integration.split(CFG_DELIMITER)[1]
                    config_to_apply = None

                    # Retrieve the integration config data to be applied from the template
                    # or the persisted org config data
                    if template:
                        config_to_apply = template[integration_name]
                    else:
                        config_to_apply = orgs[org][integration]

                    #  Not every integration has data returned and persisted
                    if len(config_to_apply):
                        update_org_integration_settings(org_id, integration_id, config_to_apply)
                        print(f"{integration_name} configuration was applied from '{my_config}' to the {org_name} organisation")
                except KeyError:
                    # The templates don't contain empty data for integrations whose config is not returned
                    # by the api and persisted.
                    pass

    except FileNotFoundError as err:
        print(err)


# Utility function to load json object from a file
def load_json_file(filename):
    f = open(filename)
    data = json.load(f)
    return data


# Function to parse the persisted config, benchmark it against the chosen template and report the differences
def report_adoption_maturity(args):
    try:
        orgs = load_json_file(args["config"])
        template_file = args['template']
        templates = dict()
        templates[f'{template_file}'] = load_json_file(f"{template_file}")
        report_file = os.path.splitext(args["config"])[0] + ".pdf"
        c = canvas.Canvas(report_file, pagesize=A4)
        write_adoption_maturity_report_template(templates, c)
        templates = load_json_file(f"{template_file}")

        for org in orgs:
            integrations = orgs[org]
            for name in integrations:
                integration = integrations[name]
                template_name = name.split(CFG_DELIMITER)[0]
                try:
                    template = templates[template_name]
                    diff = jsoncomparison.Compare().check(template, integration)
                    if len(diff):
                        print(f"Organisation {org.split(CFG_DELIMITER)[0]} - {template_name} integration configuration benchmark results against {template_file}")
                        print(json.dumps(diff, indent=4))
                        write_adoption_maturity_report_data(diff, org.split(CFG_DELIMITER)[0]+'::'+template_name, c)

                    else:
                        print(f"Organisation {org.split(CFG_DELIMITER)[0]} - {template_name} integration configuration is aligned with {template_file}")

                except KeyError as err:
                    print(f"Organisation {org.split(CFG_DELIMITER)[0]} {err} integration. Template configuration does not exist in {template_file}")

        # Save PDF
        c.save()
        print(f"PDF generated: {report_file}")

    except FileNotFoundError as err:
        print(err)


def draw_line(text, canvass, indent=0):
    global y
    if y < 2 * cm:
        canvass.showPage()
        y = height - 2 * cm
    canvass.drawString(2 * cm + indent * cm, y, text)
    y -= 0.5 * cm


# The template config data is first written to the PDF report to show the baseline against which subsequent
# reporting is done
def write_adoption_maturity_report_template(data, c):
    y = height - 2 * cm

    # Render content
    draw_line("Snyk Integrations Report", c)
    draw_line("=" * 60, c)

    for group, integrations in data.items():
        for integration, settings in integrations.items():
            if settings:
                draw_line(f"\n{group.split('::')[0]}::{integration.split('::')[0]}", c)
                for key, value in settings.items():
                    draw_line(f"{key}: {value}", c, 1)

    draw_line("=" * 60, c)
    draw_line(" " * 60, c)


# The org config compliance against the template is written to the PDF report to show non-compliance
def write_adoption_maturity_report_data(data, section_title, c):
    y = height - 2 * cm

    # Render content
    draw_line(section_title, c)
    draw_line("=" * 60, c)

    # Extract the data
    messages = extract_messages(data)
    for key, message in messages:
        draw_line(f"{key}: {message}", c, 1)

    draw_line("=" * 60, c)
    draw_line(" " * 60, c)


# Extract the json error messages to an array for rendering
def extract_messages(d, path=""):
    items = []
    for k, v in d.items():
        current_path = f"{path}.{k}" if path else k
        if isinstance(v, dict):
            if "_message" in v:
                if "Values not equal" in v["_message"]:
                    items.append((current_path, f"should be '{v['_expected']}'"))
                elif "Key does not exist" in v["_message"]:
                    items.append((current_path, f"should be '{v['_expected']}'"))
                elif "Types not equal" in v["_message"]:
                    items.append((current_path, f"should be '{v['_expected']}'"))
                else:
                    items.append((current_path, v['_message']))
            else:
                items.extend(extract_messages(v, current_path))
        else:
            pass
    return items

