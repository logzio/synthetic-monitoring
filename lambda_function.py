import datetime
import json
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
DEFAULT_DOM_COMPLETE = 5
LOGZIO_LISTENER = os.getenv("LOGZIO_LISTENER", "listener.logz.io")
LOGZIO_TOKEN = os.environ["LOGZIO_METRICS_TOKEN"]
LOGZIO_LOGS_TOKEN = os.environ["LOGZIO_LOGS_TOKEN"]
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


def _get_country_code():
    region = os.environ["AWS_REGION"]
    country_codes_by_region = {
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
        "se-east-1": "BR",
        # Canada regions
        "ca-central-1": "CA"
    }
    try:
        country_code = country_codes_by_region[region]
        return country_code
    except Exception as e:
        _send_log("{} region is not supported").format(region)
        pass

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
            _send_log("domComplete event didn't occur within the time limit")
        except Exception as e:
            _send_log("Error occurred while trying to load page: {}".format(e))
        finally:
            all_metrics = []
            # Whole DOM metric
            web_metrics = _get_page_metrics(driver, url, is_dom_complete)
            all_metrics.append(web_metrics)
            # Resource metrics
            resources = driver.execute_script("return window.performance.getEntriesByType('resource')")
            for r in resources:
                resource_metric = _get_resource_metrics(driver, url, r)
                if resource_metric:
                    all_metrics.append(resource_metric)

            if all_metrics:
                for metric in all_metrics:
                    _send_metrics(metric)
                _send_log("Sending {} metrics documents".format(len(all_metrics)))
            driver.quit()

def _get_resource_metrics(driver, url, resource):
    try:
        js_script_timestamp = "return window.performance.timing.navigationStart"
        timestamp = datetime.datetime.fromtimestamp(_ms_to_seconds(driver.execute_script(js_script_timestamp)),
                                                    tz=datetime.timezone.utc)
        data = {"@timestamp": _format_timestamp(timestamp),
                "type": "synthetic-monitoring",
                "metrics": _create_resource_metrics(resource)}
        dimensions = {"country": _get_country_code(), "region": os.environ["AWS_REGION"], "url": url,  
                      "resource_name": resource["name"], "resource_type": resource['initiatorType']}
        data["dimensions"] = dimensions
        return data
    except Exception as e:
        _send_log("Error occurred while getting resource metrics: {}".format(e))
        return {}

def _create_resource_metrics(resource):
    try:
        metrics = {}
        fetch_start = resource['fetchStart']
        response_end = resource['responseEnd']
        metrics["time_to_complete.ms"] = response_end - fetch_start
        return metrics
    except Exception as e:
        _send_log("Error creating page's metrics. {}".format(e))
        return {}

def _get_resource_response_logs(driver):
    try:
        response_logs = []
        performance_logs = driver.get_log('performance')
        for log in performance_logs:
            message = json.loads(log['message'])
            if message['message']['method'] == 'Network.responseReceived':
                response_logs.append(message['message'])
        return response_logs
    except Exception as e:
        _send_log("Error occurred while getting resource logs: {}".format(e))
        return {}

def _get_page_metrics(driver, url, is_dom_complete):
    try:
        js_script_timestamp = "return window.performance.timing.navigationStart"
        timestamp = datetime.datetime.fromtimestamp(_ms_to_seconds(driver.execute_script(js_script_timestamp)),
                                                    tz=datetime.timezone.utc)
        data = {"@timestamp": _format_timestamp(timestamp),
                "type": "synthetic-monitoring",
                "metrics": _create_metrics(driver, is_dom_complete)}
        dimensions = {"country": _get_country_code(), "region": os.environ["AWS_REGION"], "url": url}
        data["dimensions"] = dimensions
        return data
    except Exception as e:
        _send_log("Error occurred while getting page metrics: {}".format(e))
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
                _send_log("Page {} returned status code {} for region {}".format(driver.current_url, status_code,
                                                                                 os.getenv("AWS_REGION")))
        return metrics
    except Exception as e:
        _send_log("Error creating page's metrics. {}".format(e))
        return {}

def _send_metrics(metrics):
    try:
        _send_data(json.dumps(metrics))
    except Exception as e:
        _send_log("Error occurred while trying to send metrics. {}".format(e))

def _get_port_by_protocol():
    if PROTOCOL == "https":
        return "8071"
    else:
        return "8070"

def _ms_to_seconds(ms):
    return ms / 1000

def _get_dom_complete_env():
    try:
        if "DOM_COMPLETE" in os.environ:
            return float(os.getenv("DOM_COMPLETE"))
        else:
            return DEFAULT_DOM_COMPLETE
    except ValueError:
        _send_log("Error in DOM_COMPLETE value. Reverting to default DOM_COMPLETE value")
        return DEFAULT_DOM_COMPLETE

def _get_driver():
    try:
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['goog:loggingPrefs'] = {'browser': 'ALL', 'performance': 'ALL'}
        options = webdriver.ChromeOptions()
        # TODO: check for more options
        lambda_options = [
            '--autoplay-policy=user-gesture-required',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-breakpad',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-default-apps',
            '--disable-dev-shm-usage',
            '--disable-domain-reliability',
            '--disable-extensions',
            '--disable-features=AudioServiceOutOfProcess',
            '--disable-hang-monitor',
            '--disable-ipc-flooding-protection',
            '--disable-notifications',
            '--disable-offer-store-unmasked-wallet-cards',
            '--disable-popup-blocking',
            '--disable-print-preview',
            '--disable-prompt-on-repost',
            '--disable-renderer-backgrounding',
            '--disable-setuid-sandbox',
            '--disable-speech-api',
            '--disable-sync',
            '--disk-cache-size=33554432',
            '--hide-scrollbars',
            '--ignore-gpu-blacklist',
            '--ignore-certificate-errors',
            '--metrics-recording-only',
            '--mute-audio',
            '--no-default-browser-check',
            '--no-first-run',
            '--no-pings',
            '--no-sandbox',
            '--no-zygote',
            '--password-store=basic',
            '--use-gl=swiftshader',
            '--use-mock-keychain',
            '--single-process',
            '--headless']
        for argument in lambda_options:
            options.add_argument(argument)
        options.binary_location = "/opt/bin/chromium"
        driver = webdriver.Chrome(desired_capabilities=desired_capabilities, options=options)
        return driver
    except Exception as e:
        _send_log("Error creating web driver. {}".format(e))
        return {}

def _get_status(logs):
    for log in logs:
        if log['message']:
            d = json.loads(log['message'])
            try:
                content_type = 'text/html' in d['message']['params']['response']['headers']['content-type']
                response_received = d['message']['method'] == 'Network.responseReceived'
                if content_type and response_received:
                    return d['message']['params']['response']['status']
            except:
                pass

def _get_page_status_code(driver):
    try:
        performance_logs = driver.get_log('performance')
        status_code = _get_status(performance_logs)
        return int(status_code)
    except Exception as e:
        _send_log("Error occurred while getting performance logs: {}".format(e))
        return {}

def _send_log(message):
    timestamp = _format_timestamp(datetime.datetime.now(tz=datetime.timezone.utc))
    log = {"@timestamp": timestamp, "message": message, "type": "synthetic-monitoring", "lambda_function":os.environ["AWS_LAMBDA_FUNCTION_NAME"], "region":os.environ["AWS_REGION"], "url":os.environ["URL"]}
    _send_data(json.dumps(log), is_metrics=False)

def _send_data(data, is_metrics=True):
    try:
        port = _get_port_by_protocol()
        token = LOGZIO_TOKEN if is_metrics else LOGZIO_LOGS_TOKEN
        url = "{}://{}:{}/?token={}".format(PROTOCOL, LOGZIO_LISTENER, port, token)
        response = requests.post(url, data=data)
        if not response.ok:
            # TODO
            pass
    except Exception as e:
        # TODO
        pass

def _format_timestamp(timestamp):
    return "{}Z".format(timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3])

def _get_url():
    try:
        return os.environ["URL"]
    except KeyError:
        _send_log("Error - no URL entered")
        return {}

def lambda_handler(event, context):
    url = _get_url()
    if url:
        _monitor(url)
