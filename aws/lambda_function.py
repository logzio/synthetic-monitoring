import os
import sys
import threading

sys.path.append(".")
from lights import LightsMonitor
import input_validator

threads = []


def lambda_handler(event, context):
    urls_str = os.getenv("URL")
    logs_token = os.getenv("LOGZIO_LOGS_TOKEN")
    metrics_token = os.getenv("LOGZIO_METRICS_TOKEN")
    logzio_region_code = os.getenv("LOGZIO_REGION", "")
    logzio_custom_listener = os.getenv("LOGZIO_CUSTOM_LISTENER", "")
    aws_region = os.getenv("AWS_REGION")
    function_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME")

    if is_valid_input(logs_token, metrics_token, logzio_region_code, aws_region, function_name):
        urls = create_and_validate_url_list(urls_str)

        for url in urls:
            t = threading.Thread(target=create_and_run_lights,
                                 args=(url, logs_token, metrics_token, logzio_region_code,
                                       aws_region, function_name, logzio_custom_listener))
            threads.append(t)
            t.start()

        for thread in threads:
            thread.join()


def is_valid_input(logs_token, metrics_token, logzio_region_code, aws_region, func_name):
    try:
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


def create_and_run_lights(url, logs_token, metrics_token, logzio_region_code, aws_region, function_name,
                          custom_listener):
    lights_monitor = LightsMonitor(url=url,
                                   logs_token=logs_token,
                                   metrics_token=metrics_token,
                                   logzio_region_code=logzio_region_code,
                                   logzio_listener=custom_listener,
                                   region=aws_region,
                                   function_name=function_name,
                                   system="aws")
    lights_monitor.monitor()


def create_and_validate_url_list(urls_str):
    try:
        urls = [url.strip() for url in urls_str.split(",")]
    except ValueError as e:
        raise ValueError("Can't start monitoring. Error while getting URLs: {}".format(e))
    return input_validator.validate_url_list(urls)
