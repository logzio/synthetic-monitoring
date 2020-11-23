import os
import sys
sys.path.append(".")
from lambda_function.lights import LightsMonitor
import lambda_function.input_validator


def lambda_handler(event, context):
    url = os.getenv("URL")
    logs_token = os.getenv("LOGZIO_LOGS_TOKEN")
    metrics_token = os.getenv("LOGZIO_METRICS_TOKEN")
    logzio_region_code = os.getenv("LOGZIO_REGION", "")
    logzio_custom_listener = os.getenv("LOGZIO_CUSTOM_LISTENER", "")
    aws_region = os.getenv("AWS_REGION")
    function_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME")

    if is_valid_input(url, logs_token, metrics_token, logzio_region_code, aws_region, function_name):
        lights_monitor = LightsMonitor(url=url,
                                       logs_token=logs_token,
                                       metrics_token=metrics_token,
                                       logzio_region_code=logzio_region_code,
                                       logzio_listener=logzio_custom_listener,
                                       region=aws_region,
                                       function_name=function_name,
                                       system="aws")

        lights_monitor.monitor()


def is_valid_input(url, logs_token, metrics_token, logzio_region_code, aws_region, func_name):
    try:
        input_validator.is_valid_url(url)
        input_validator.is_valid_logzio_token(logs_token)
        input_validator.is_valid_logzio_token(metrics_token)
        input_validator.is_valid_logzio_region_code(logzio_region_code)
        input_validator.is_valid_system_region("aws", aws_region)
        input_validator.is_valid_function_name(func_name)
        return True
    except (ValueError, TypeError) as e:
        print("Could not launch monitor, invalid input: {}".format(e))
    except Exception as e:
        print("Unexpected error occurred, could not launch monitor: {}".format(e))
    return False
