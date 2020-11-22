import os
import sys
sys.path.append(".")
from lambda_function.lights import LightsMonitor


def lambda_handler(event, context):
    url = os.getenv("URL")
    logs_token = os.getenv("LOGZIO_LOGS_TOKEN")
    metrics_token = os.getenv("LOGZIO_METRICS_TOKEN")
    logzio_region_code = os.getenv("LOGZIO_REGION", "")
    logzio_custom_listener = os.getenv("LOGZIO_CUSTOM_LISTENER", "")
    region = os.getenv("AWS_REGION")
    function_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME")

    lights_monitor = LightsMonitor(url=url,
                                   logs_token=logs_token,
                                   metrics_token=metrics_token,
                                   logzio_region_code=logzio_region_code,
                                   logzio_listener=logzio_custom_listener,
                                   region=region,
                                   function_name=function_name,
                                   system="aws")

    lights_monitor.monitor()
