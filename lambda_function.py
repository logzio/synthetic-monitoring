import chromedriver_binary
import datetime
import json
import logging
import os
import re
import requests
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

FAILED_STATUS_CODE = -1
SUCCESS = 1
FAILURE = 0
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
    driver = _get_driver()
    if driver:
        is_dom_complete = False
        try:
            driver.get(url)
            wait = WebDriverWait(driver, dom_to_complete_sec)
            check_dom = dom_is_completed()
            is_dom_complete = wait.until(check_dom)
        except exceptions.TimeoutException:
            logger.info("domComplete event didn't occur within the time limit")
        finally:
            web_metrics = _get_page_metrics(driver, url, is_dom_complete)
            if web_metrics:
                _send_metrics(web_metrics)
                logger.debug("Metrics were sent from region: {}, url: {}".format(os.environ["region"], url))
            driver.quit()


def _get_network_data(driver):
    try:
        js_script = "var performance = window.performance || window.mozPerformance || window.msPerformance || " \
                    "window.webkitPerformance || {}; var network = performance.getEntries() || {}; return network; "
        network_data = driver.execute_script(js_script)
        return network_data
    except Exception as e:
        logger.error("Error occurred while getting page metrics. {}".format(e))
        return {}


def _get_page_metrics(driver, url, is_dom_complete):
    try:
        js_script_timestamp = "return window.performance.timing.navigationStart"
        timestamp = datetime.datetime.fromtimestamp(_ms_to_seconds(driver.execute_script(js_script_timestamp)), tz=datetime.timezone.utc)
        timestamp_str = "{}Z".format(timestamp.strftime("%Y-%m-%dT%H:%M:s%S.%f")[:-3])
        data = {"@timestamp": timestamp_str,
                "type": "synthetic-monitoring",
                "metrics": _create_metrics(driver, is_dom_complete)}
        dimensions = {"region": os.environ["region"], "url": url}
        data["dimensions"] = dimensions
        return data
    except Exception as e:
        logger.error("Error occurred while getting page metrics: {}".format(e))
        return {}


def _create_metrics(driver, is_dom_complete):
    try:
        metrics = {}
        navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
        request_start = driver.execute_script("return window.performance.timing.requestStart")
        response_start = driver.execute_script("return window.performance.timing.responseStart")
        if is_dom_complete:
            dom_complete = driver.execute_script("return window.performance.timing.domComplete")
            metrics["time_to_complete.ms"] = dom_complete - navigation_start
        metrics["time_to_first_byte.ms"] = response_start - request_start
        metrics["dom_is_complete"] = 1 if is_dom_complete else 0
        status_code = _get_page_status_code(driver)
        if status_code:
            metrics["status_code"] = status_code
            if 200 <= status_code < 300:
                metrics["up"] = SUCCESS
            elif 400 <= status_code < 600:
                metrics["up"] = FAILURE
        return metrics
    except Exception as e:
        logger.error("Error creating page's metrics. {}".format(e))
        return {}


def _send_metrics(metrics):
    try:
        metrics_json = json.dumps(metrics)
        logger.debug(metrics_json)
        port = _get_port_by_protocol()
        url = "{}://{}:{}/?token={}".format(PROTOCOL, LOGZIO_LISTENER, port, LOGZIO_TOKEN)
        response = requests.post(url, data=metrics_json)
        if response.ok:
            logger.debug("Metrics sent successfully.")
        else:
            logger.error("Couldn't send metrics. Response code from logzio: {}. {}".format(response.status_code, response.text))
    except Exception as e:
        logger.error("Error occurred while trying to send metrics. {}".format(e))


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


def _get_driver():
    try:
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['goog:loggingPrefs'] = {'browser': 'ALL', 'performance': 'ALL'}
        options = webdriver.ChromeOptions()
        # TODO: check for more options
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        chromedriver_binary.add_chromedriver_to_path()
        options.binary_location = chromedriver_binary.chromedriver_filename
        # driver = webdriver.Chrome(desired_capabilities=desired_capabilities, options=options, executable_path=chromedriver_binary.chromedriver_filename)
        driver = webdriver.Chrome(desired_capabilities=desired_capabilities, options=options)
        return driver
    except Exception as e:
        logger.error("Error creating web driver. {}".format(e))
        return {}


def _get_page_status_code(driver):
    try:
        performance_logs = driver.get_log('performance')
        response = next(json.loads(log["message"]) for log in performance_logs if "headersText" in log["message"])
        status_code = _extract_status_code_from_response(response)
        return status_code
    except Exception as e:
        logger.error("Error occurred while getting performance logs: {}".format(e))
        return {}


def _extract_status_code_from_response(response):
    try:
        status_code_line = response["message"]["params"]["headersText"].split("\r\n")[0]
        line_regex = r"HTTP/1.1\s(\d{3})\s.*"
        status_code_index = re.search(line_regex, status_code_line).regs[1]
        status_code = status_code_line[status_code_index[0]:status_code_index[1]]
        return int(status_code)
    except Exception as e:
        logger.error("Error getting page's status code. {}".format(e))
        return {}


logger = _create_logger()
# _monitor("https://www.logz.io")


def lambda_handler(event, context):
    _monitor("https://www.logz.io")
