import sys, getopt, os, snyk
from yaspin import yaspin
from helperFunctions import *
import time

helpString ='''--help : Returns this page \n--force : By default this script will perform a dry run, add this flag to actually apply changes\n--delete : By default this script will deactive projects, add this flag to delete\n--delete-non-active-projects : By default this script will deactivate projects, add this flag to delete active AND non-active projects instead \n--origins : Defines origin types of projects to delete\n--orgs : A set of orgs upon which to perform delete,be sure to use org slug instead of org display name (use ! for all orgs)\n--scatypes : Defines SCA type/s of projects to deletes \n--products : Defines product/s types of projects to delete\n--delete-empty-orgs : This will delete all orgs that do not have any projects in them \n* Please replace spaces with dashes(-) when entering orgs \n* If entering multiple values use the following format: "value-1 value-2 value-3"
            '''

#get all user orgs and verify snyk API token
userOrgs = []
client = snyk.SnykClient(os.getenv("SNYK_TOKEN"))
try:
    userOrgs = client.organizations.all()
except snyk.errors.SnykHTTPError as err:
    print("💥 Ran into an error while fetching account details, please check your API token")
    print( helpString)

def main(argv):
    inputOrgs = []
    products = []
    scaTypes = []
    origins = []
    deleteorgs = False
    dryrun = True
    deactivate = True
    deleteNonActive = False

    
    #valid input arguments declared here
    try:
        opts, args = getopt.getopt(argv, "hofd",["help", "orgs=", "sca-types=", "products=", "origins=", "force", "delete-empty-orgs", "delete", "delete-non-active-projects"] )
    except getopt.GetoptError:
        print("Error parsing input, please check your syntax")
        sys.exit(2)
    
    #process input
    for opt, arg in opts:
        if opt == '--help':
            print(helpString)
            sys.exit(2)
        if opt =='--orgs':
            if arg == "!":
                inputOrgs = [org.slug for org in userOrgs]
            else:
                inputOrgs = arg.split()
        if opt == '--sca-types':
            scaTypes = [scaType.lower() for scaType in arg.split()]
        if opt == '--products':
            print(arg)
            products =[product.lower() for product in arg.split()]
        if opt == '--origins':
            origins =[origin.lower() for origin in arg.split()]
        if opt =='--delete-empty-orgs':
            deleteorgs = True
        if opt =='--force':
            dryrun = False
        if opt =='--delete':
            deactivate = False
        if opt =='--delete-non-active-projects':
            deactivate = False
            deleteNonActive = True
    #error handling if no filters declared
    filtersEmpty = len(scaTypes) == 0 and len(products) == 0 and len(origins) == 0
    if filtersEmpty and not deleteorgs:
        print(filtersEmpty)
        print("No settings entered, exiting")
        print(helpString)
        sys.exit(2)
    
    #error handling if no orgs declared
    if len(inputOrgs) == 0:
        print("No orgs to process entered, exiting")
        print(helpString)
    
    #print dryrun message
    if dryrun:
        print("\033[93mTHIS IS A DRY RUN NOTHING, WILL BE DELETED! USE --FORCE TO APPLY ACTIONS\u001b[0m")
    
    #delete functionality
    for currOrg in userOrgs:

        #if curr org is in list of orgs to process
        if currOrg.slug in inputOrgs:

            #remove currorg for org proccesing list and print proccesing message
            inputOrgs.remove(currOrg.slug)
            print("Processing" + """ \033[1;32m"{}" """.format(currOrg.name) + "\u001b[0morganization")

            #cycle through all projects in current org and delete projects that match filter
            for currProject in currOrg.projects.all():


                #variables which determine whether project matches criteria to delete, if criteria is empty they will be defined as true
                scaTypeMatch = False
                originMatch = False
                productMatch = False
                isActive = currProject.isMonitored

                #if scatypes are not declared or curr project type matches filter criteria then return true
                if len(scaTypes) != 0:
                    if currProject.type in scaTypes:
                        scaTypeMatch = True
                else:
                    scaTypeMatch = True

                #if origintypes are not declared or curr project origin matches filter criteria then return true
                if len(origins) != 0:
                    if currProject.origin in origins:
                        originMatch = True
                else:
                    originMatch = True

                #if producttypes are not declared or curr project product matches filter criteria then return true
                currProjectProductType = convertTypeToProduct(currProject.type)
                if len(products) != 0:
                    if currProjectProductType in products:
                        productMatch = True
                else:
                    productMatch = True  
                
                #delete project if filter are meet
                if scaTypeMatch and originMatch and productMatch and (isActive or deleteNonActive) and not filtersEmpty:
                    currProjectDetails = f"Origin: {currProject.origin}, Type: {currProject.type}, Product: {currProjectProductType}"
                    action =  "Deactivating" if deactivate else "Deleting"
                    spinner = yaspin(text=f"{action}\033[1;32m {currProject.name}", color="yellow")
                    spinner.write(f"\u001b[0m    Processing project: \u001b[34m{currProjectDetails}\u001b[0m, Status Below👇")
                    spinner.start()
                    try:
                        if not dryrun:
                            if not deactivate:
                                currProject.delete()
                            else:
                                currProject.deactivate()
                        spinner.ok("✅ ")
                    except exception as e:
                        spinner.fail("💥 ")

            #if org is empty and --delete-empty-org flag is on
            if len(currOrg.projects.all()) == 0 and deleteorgs:
                spinner = yaspin(text="Deleting\033[1;32m {}\u001b[0m since it is an empty organization".format(currOrg.name), color="yellow")
                spinner.start()
                try:
                    if not dryrun:
                        client.delete(f'org/{currOrg.id}')
                    spinner.ok("✅ ")
                    spinner.stop()
                except:
                    spinner.fail("💥 ")
                    spinner.stop()                       
    #process input orgs which didnt have a match
    if len(inputOrgs) != 0:
        print("\033[1;32m{}\u001b[0m are organizations which do not exist or you don't have access to them, please check your spelling, insure that spaces are replaced with dashes, and that you are using org slugs rather then display names".format(inputOrgs))
                
    if dryrun:
        print("\033[93mDRY RUN COMPLETE NOTHING DELETED")


                    
            
main(sys.argv[1:])

