import os
import sys
sys.path.append(".")
from lights import LightsMonitor


def lambda_handler(event, context):
    url = os.getenv("URL")
    logs_token = os.getenv("LOGZIO_LOGS_TOKEN")
    metrics_token = os.getenv("LOGZIO_METRICS_TOKEN")
    logzio_region_code = os.getenv("LOGZIO_REGION", "")
    logzio_custom_listener = os.getenv("LOGZIO_CUSTOM_LISTENER", "")
    region = os.getenv("AWS_REGION")
    function_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    protocol = os.getenv("PROTOCOL", "https")
    max_dom_complete_str = os.getenv("DOM_COMPLETE", "")

    max_dom_complete = 5.0
    if max_dom_complete_str != "":
        max_dom_complete = float(max_dom_complete_str)

    lights_monitor = LightsMonitor(url=url,
                                   logs_token=logs_token,
                                   metrics_token=metrics_token,
                                   logzio_region_code=logzio_region_code,
                                   logzio_listener=logzio_custom_listener,
                                   region=region,
                                   function_name=function_name,
                                   max_dom_complete=max_dom_complete,
                                   protocol=protocol,
                                   system="aws")

    lights_monitor.monitor()
