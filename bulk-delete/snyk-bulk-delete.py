import sys, getopt, os, snyk
from yaspin import yaspin
from helperFunctions import *

helpString ='''--help/-h : Returns this page \n--dryrun : Add this flag to perform a dry run of script which doesn't actually delete any projects \n--origins : Defines origin types of projects to delete\n--orgs/-o : A set of orgs upon which to perform delete (use * for all orgs)\n--scatypes : Defines SCA type/s of projects to deletes \n--products : Defines product/s types of projects to delete \n* Please replace spaces with dashes(-) when entering orgs \n* If entering multiple values use the following format: "value-1 value-2 value-3"
            '''

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
    dryrun = False
    
    #valid input arguments
    try:
        opts, args = getopt.getopt(argv, "ho:", ["help", "orgs=", "sca-types=", "products=", "origins=", "dry-run", "delete-empty-orgs"] )
    except getopt.GetoptError:
        print("Error parsing input, please check your syntax")
        sys.exit(2)
    

    #process input
    for opt, arg in opts:
        if opt == '-h' or opt == '--help':
            print(helpString)
            sys.exit(2)
        if opt == '-o' or opt =='--orgs':
            if arg == "!":
                inputOrgs = [org.name for org in userOrgs]
            else:
                inputOrgs = arg.split()
        if opt == '--sca-types':
            scaTypes = [scaType.lower() for scaType in arg.split()]
        if opt == '--products':
            products =[product.lower() for product in arg.split()]
        if opt == '--origins':
            origins =[origin.lower() for origin in arg.split()]
        if opt == '--dry-run':
            dryrun = True
        if opt == '--delete-empty-orgs':
            deleteorgs = True
    
    if len(scaTypes) == 0 and len(products) == 0 and len(origins) == 0 and not deleteorgs:
        print(origins)
        print("No delete settings entered, exiting")
        print(helpString)
        sys.exit(2)
    
    if len(inputOrgs) == 0:
        print("No orgs to process entered, exiting")
        print(helpString)
    
    if dryrun:
        print("\033[93m!!THIS IS A DRY RUN NOTHING WILL BE DELETED!!\u001b[0m")
    #delete functionality
    for currOrg in userOrgs:
        if currOrg.name in inputOrgs:
            inputOrgs.remove(currOrg.name)
            print("Processing" + """ \033[1;32m"{}" """.format(currOrg.name) + "\u001b[0morganization")
            for currProject in currOrg.projects.all():
                #if sca type matches user input
                if currProject.type in (scaTypes):
                    spinner = yaspin(text="Deleting\033[1;32m {}\u001b[0m since it is a \u001b[34m{}\u001b[0m project".format(currProject.name, currProject.type), color="yellow")
                    spinner.start()
                    try:
                        if not dryrun:
                            currProject.delete()
                        spinner.ok("✅ ")
                        spinner.stop()
                    except:
                        spinner.fail("💥 ")
                        spinner.stop()    
                #if product matches user input
                if len(products):
                    productType = convertTypeToProduct(currProject.type)
                    spinner = yaspin(text="Deleting\033[1;32m {}\u001b[0m since it is a \u001b[34m{}\u001b[0m project".format(currProject.name, productType), color="yellow")
                    if productType in products:
                        spinner.start()
                        try:
                            if not dryrun:
                                currProject.delete()
                            spinner.ok("✅ ")
                            spinner.stop()
                        except exception as e:
                            spinner.fail("💥 ")
                            spinner.stop()
                        spinner.stop()
                #if origin matches user input
                if currProject.origin in (origins):
                    spinner = yaspin(text="Deleting\033[1;32m {}\u001b[0m since it is a \u001b[34m{}\u001b[0m project".format(currProject.name, currProject.origin), color="yellow")
                    spinner.start()
                    try:
                        if not dryrun:
                            currProject.delete()
                        spinner.ok("✅ ")
                        spinner.stop()
                    except:
                        spinner.fail("💥 ")
                        spinner.stop()    
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
        print("\033[1;32m{}\u001b[0m are organizations which do not exist or you don't have access to them, please check your spelling and insure that spaces are replaced with dashes".format(inputOrgs))
                
    if dryrun:
        print("\033[93mDRY RUN COMPLETE NOTHING DELETED")


                    
            
main(sys.argv[1:])

