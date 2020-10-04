import json
import logging
import os
import requests
import time
import traceback
import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

CHROME_DRIVER_PATH = os.environ["CHROME_DRIVER_PATH"]
FAILED_STATUS_CODE = -1
PAGE_IS_UP = 1
PAGE_IS_DOWN = 0
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DOM_COMPLETE = 5
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOGZIO_LISTENER = os.getenv("LOGZIO_LISTENER", "listener.logz.io")
LOGZIO_TOKEN = os.environ["LOGZIO_TOKEN"]
PROTOCOL = os.getenv("PROTOCOL", "https")


def _get_status_ready(driver):
    js_script = "return document.readyState"
    ready_response = driver.execute_script(js_script)
    return ready_response == 'complete'


class dom_is_completed(object):
    """An expectation for checking that the DOM elements load is complete.
  """

    def __init__(self):
        pass

    def __call__(self, driver):
        return _get_status_ready(driver)


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
    dom_to_complete_sec = _get_dom_complete_env()
    driver = webdriver.Chrome(CHROME_DRIVER_PATH)
    is_dom_complete = False
    try:
        driver.get(url)
        wait = WebDriverWait(driver, dom_to_complete_sec)
        check_dom = dom_is_completed()
        is_dom_complete = wait.until(check_dom)
        # web_metrics = _get_page_metrics(driver, url)
        # if web_metrics:
        #     _send_metrics(web_metrics)
        #     logger.debug("Metrics were sent from region: {}, url: {}".format(os.environ["region"], url))
    except selenium.common.exceptions.TimeoutException:
        logger.error("domComplete event didn't occur within the time limit")
        # TODO: SEND METRICS INDICATING THAT ERROR
    except Exception as e:
        logger.error("Error opening url: {}".format(traceback.print_exception()))
    finally:
        web_metrics = _get_page_metrics(driver, url, is_dom_complete)
        if web_metrics:
            _send_metrics(web_metrics)
            logger.debug("Metrics were sent from region: {}, url: {}".format(os.environ["region"], url))
        driver.quit()


def _get_network_data(driver):
    try:
        js_script = "var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {}; var network = performance.getEntries() || {}; return network;"
        network_data = driver.execute_script(js_script)
        return network_data
    except Exception as e:
        logger.error("Error occurred while getting page metrics: {}".format(traceback.print_exception()))
        return {}


def _get_page_metrics(driver, url, is_dom_complete):
    try:
        data = {}
        metrics = {}
        navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
        navigation_start_seconds = _ms_to_seconds(navigation_start)
        request_start = driver.execute_script("return window.performance.timing.requestStart")
        response_start = driver.execute_script("return window.performance.timing.responseStart")
        if is_dom_complete:
            dom_complete = driver.execute_script("return window.performance.timing.domComplete")
            metrics["time_to_complete.ms"] = dom_complete - navigation_start
        data["@timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(navigation_start_seconds))
        data["type"] = "synthetic-monitoring"
        metrics["time_to_first_byte.ms"] = response_start - request_start
        metrics["dom_is_complete"] = 1 if is_dom_complete else 0
        # TODO: determine if page is up or down:
        # metrics["up"] = PAGE_IS_UP if dom_complete else PAGE_IS_DOWN
        data["metrics"] = metrics
        dimensions = {"region": os.environ["region"], "url": url}
        data["dimensions"] = dimensions
        return data
    except Exception as e:
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


def _ms_to_seconds(ms):
    return ms / 1000


def _get_dom_complete_env():
    try:
        if "DOM_COMPLETE" in os.environ:
            return int(os.getenv("DOM_COMPLETE"))
        else:
            return DEFAULT_DOM_COMPLETE
    except ValueError:
        logger.error("Error in DOM_COMPLETE value. Reverting to default DOM_COMPLETE value")
        return DEFAULT_DOM_COMPLETE


logger = _create_logger()
_monitor("https://www.logz.io")
# _monitor("http://the-internet.herokuapp.com/status_codes/404")


# def handler(event, context):
#     _monitor("https//www.youtube.com")
