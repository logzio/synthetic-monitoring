import json
import logging
import os
import requests
import traceback
from selenium import webdriver


CHROME_DRIVER_PATH = os.environ["CHROME_DRIVER_PATH"]
FAILED_STATUS_CODE = -1
PAGE_IS_UP = 1
PAGE_IS_DOWN = 0
DEFAULT_LOG_LEVEL = "INFO"
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOGZIO_LISTENER = os.getenv("LOGZIO_LISTENER", "listener.logz.io")
LOGZIO_TOKEN = os.environ["LOGZIO_TOKEN"]
PROTOCOL = os.getenv("PROTOCOL", "https")


def _create_logger():
    try:
        user_level = os.environ["LOGZIO_LOG_LEVEL"].upper()
        level = user_level if user_level in LOG_LEVELS else DEFAULT_LOG_LEVEL
    except KeyError:
        level = DEFAULT_LOG_LEVEL
    logging.basicConfig(format='%(asctime)s\t\t%(levelname)s\t[%(name)s]\t%(filename)s:%(lineno)d\t%(message)s',
                        level=level)
    return logging.getLogger(__name__)


def _monitor(url):
    try:
        driver = webdriver.Chrome(CHROME_DRIVER_PATH)
        driver.get(url)
        web_metrics = _get_page_metrics(driver, url)
        if web_metrics:
            _send_metrics(web_metrics)
            logger.debug("Metrics were sent from region: {}, url: {}".format(os.environ["region"], url))
        driver.quit()
    except Exception as e:
        logger.error("Error opening web driver: {}".format(traceback.print_exception()))
        # TODO: GET PAGE'S STATUS CODE


def _get_page_metrics(driver, url):
    try:
        data = {}
        metrics = {}
        navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
        request_start = driver.execute_script("return window.performance.timing.requestStart")
        response_end = driver.execute_script("return window.performance.timing.responseEnd")
        load_end = driver.execute_script("return window.performance.timing.domComplete")
        data["@timestamp"] = navigation_start
        data["type"] = "synthetic-monitoring"
        metrics["time_to_first_byte.ms"] = response_end - request_start
        metrics["time_to_complete.ms"] = load_end - navigation_start
        metrics["up"] = PAGE_IS_UP if load_end else PAGE_IS_DOWN
        data["metrics"] = metrics
        dimensions = {"region": os.environ["region"], "url": url}
        data["dimensions"] = dimensions
        return data
    except Exception as e:
        # TODO: CHECK
        logger.error("Error occurred while getting page metrics: {}".format(traceback.print_exception()))
        return {}


def _send_metrics(metrics):
    try:
        metrics_json = json.dumps(metrics)
        print(metrics_json)
        port = _get_port_by_protocol()
        url = "{}://{}:{}/?token={}".format(PROTOCOL, LOGZIO_LISTENER, port, LOGZIO_TOKEN)
        response = requests.post(url, data=metrics_json)
        if response.ok:
            logger.debug("Metrics sent successfully.")
        else:
            logger.error("Couldn't send metrics. Response code from logzio: {}. {}".format(response.status_code, response.text))
    except Exception as e:
        logger.error("Error occurred while trying to send metrics: {}".format(traceback.print_exception()))


def _get_port_by_protocol():
    if PROTOCOL is "https":
        return "8071"
    else:
        return "8070"


logger = _create_logger()
_monitor("https://www.logz.io")

# def handler(event, context):
#     _monitor("https//www.youtube.com")
