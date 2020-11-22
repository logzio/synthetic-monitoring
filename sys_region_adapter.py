"""
This module is for coordinating between the regions and systems that the lightS project supports
"""

SUPPORTED_SYSTEMS = ["aws", "none"]
AWS_REGION_TO_COUNTRY_CODE = {
    # US regions
    "us-east-1": "US",
    "us-east-2": "US",
    "us-west-1": "US",
    "us-west-2": "US",
    # Africa regions
    "af-south-1": "ZA",
    # Asia regions
    "ap-east-1": "HK",
    "ap-south-1": "IN",
    "ap-northeast-2": "KR",
    "ap-southeast-1": "SG",
    "ap-southeast-2": "AU",
    "ap-northeast-1": "JP",
    # EU regions
    "eu-central-1": "DE",
    "eu-west-1": "IE",
    "eu-west-2": "GB",
    "eu-south-1": "IT",
    "eu-west-3": "FR",
    "eu-north-1": "SE",
    # Middle east regions
    "me-south-1": "BH",
    # South america regions
    "sa-east-1": "BR",
    # Canada regions
    "ca-central-1": "CA"
}


# validate_system checks that a given system name is in the supported systems list
def validate_system(system):
    if type(system) is not str:
        raise TypeError("System should be a string")
    if system not in SUPPORTED_SYSTEMS:
        raise ValueError("Unsupported system: {}".format(system))
    return True


# validate_region_by_system checks if a given region is one of the supported regions of the chosen system.
# the function sends the region and the corresponding system region list to __validate_region
def validate_region_by_system(system, region):
    if type(region) is not str:
        raise TypeError("Region should be a string")
    if system == "aws":
        return __validate_region(region, AWS_REGION_TO_COUNTRY_CODE.keys())
    if system == "none":
        return True
    raise ValueError("Unsupported region: {} for system: {}".format(region, system))


# __validate_region checks if a region is in a given region list
def __validate_region(region, regions_list):
    if region not in regions_list:
        raise ValueError("Unsupported region: {}".format(region))


# get_country_code_by_region returns the country code of the region, by calling __get_country_code with the chosen
# system's region list
def get_country_code_by_region_and_system(system, region):
    if system == "aws":
        return __get_country_code(region, AWS_REGION_TO_COUNTRY_CODE)
    if system == "none":
        return "US"


# __get_country_code returns the country code of a region
def __get_country_code(region, region_to_code_dict):
    if region not in region_to_code_dict:
        raise ValueError("Unsupported region: {}".format(region))
    return region_to_code_dict[region]
