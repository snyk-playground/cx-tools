#converts API types into a snyk product
def convertTypeToProduct(inputType):
    containerTypes = ["deb", "linux", "dockerfile", "rpm", "apk"]
    iacTypes = ["k8sconfig", "helmconfig", "terraformconfig", "armconfig", "cloudformationconfig"]
    codeTypes = ["sast"]

    if inputType in containerTypes:
        return "container"
    elif inputType in iacTypes:
        return "iac"
    elif inputType in codeTypes:
        return "code"
    else:
        return "open source"