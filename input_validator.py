"""
This module is for validating user's input
"""

import re
import sys
sys.path.append('.')
import sys_region_adapter


# is_valid_logzio_token checks if a given token is a valid logz.io token
def is_valid_logzio_token(token):
    if type(token) is not str:
        raise TypeError("Token should be a string")
    regex = r"\b[a-zA-Z]{32}\b"
    match_obj = re.search(regex, token)
    if match_obj is not None and match_obj.group() is not None:
        if any(char.islower() for char in token) and any(char.isupper() for char in token):
            return True
    raise ValueError("Invalid token: {}".format(token))


# is_valid_logzio_region_code checks that a the region code is a valid logzio region code.
# an empty string ("") is also acceptable
def is_valid_logzio_region_code(logzio_region_code):
    if logzio_region_code is None or type(logzio_region_code) is not str:
        raise TypeError("Logzio region code should be a string")
    valid_logzio_regions = ["au", "ca", "eu", "nl", "uk", "us", "wa"]
    if logzio_region_code != "":
        if logzio_region_code not in valid_logzio_regions:
            raise ValueError("invalid logzio region code: {}. cannot start monitoring".format(logzio_region_code))
    return True


# is_supported system checks that a system is supported
def is_supported_system(system):
    return sys_region_adapter.validate_system(system)


# validate_url_list checks that the urls list is not empty and that the urls are valid, and returns the final list
# with the valid urls.
# Invalid url will not be monitored.
def validate_url_list(urls):
    if urls is not None and type(urls) is not list:
        raise TypeError("URL should be a list")
    if len(urls) == 0:
        raise ValueError("Cannot start monitoring, should include at least one url to monitor.")
    valid_urls = []
    for url in urls:
        try:
            is_valid_url(url)
            valid_urls.append(url)
        except (ValueError, TypeError) as e:
            print("Can't monitor url: {}.\n{}".format(url, e))
        except Exception as e:
            print("Can't monritor url: {}.\nUnexpected error occured: {}".format(url, e))

    if len(valid_urls) == 0:
        raise ValueError("Couldn't find any valid urls. Can't start monitoring.")
    return valid_urls


# is_valid_url checks with a regex that a url is in a valid format
def is_valid_url(url):
    if type(url) is not str:
        raise TypeError("URL should be a string")
    regex = '^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$'
    match_obj = re.search(regex, url)
    if match_obj is not None and match_obj.group() is not None:
        return True
    raise ValueError("URL is invalid: {}".format(url))


# is_valid_system_region checks if a region is supported by the system
def is_valid_system_region(system, region):
    return sys_region_adapter.validate_region_by_system(system, region)


# is_valid_function_name checks if the function name is a string
def is_valid_function_name(function_name):
    if function_name is not None and type(function_name) is not str:
        raise TypeError("Function name should be a string")
    return True


# is_valid_max_dome_complete checks if max_dom_complete is a non-zero, positive float
def is_valid_max_dom_complete(max_dom_complete):
    if max_dom_complete is None or type(max_dom_complete) is not float:
        raise TypeError()
    elif max_dom_complete <= 0:
        raise ValueError("Invalid max_dom_complete value. Should be non-zero, positive number")
    return True


# validate_aws_scrape_interval validates the scrape interval for the lambda functions
def validate_aws_scrape_interval(scrape_interval):
    if scrape_interval is None or scrape_interval == "":
        raise ValueError("Must enter value scrape interval")
    if scrape_interval is not None and type(scrape_interval) is not str:
        raise TypeError("Invalid type for scrape interval")
    regex = r'^rate\([0-9]+ (minute|minutes|hour|hours|day|days)\)$'
    match_obj = re.search(regex, scrape_interval)
    if match_obj is not None and match_obj.group() is not None:
        return True
    else:
        raise ValueError("Invalid value for scrape interval: {}".format(scrape_interval))
