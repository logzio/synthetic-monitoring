from dataclasses import dataclass
import datetime
import json
import requests
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import sys
sys.path.append(".")
import input_validator
from sys_region_adapter import get_country_code_by_region_and_system


@dataclass()
class LightsMonitor(object):
    """
    Object for creating and sending web page metrics to logz.io
    """
    # class constants:
    SUCCESS = 1
    FAILURE = 0
    TOKEN_LENGTH = 32
    MAX_DOM_COMPLETE = 5.0

    url: str
    metrics_token: str
    logs_token: str
    region: str
    logzio_region_code: str
    logzio_listener: str
    function_name: str
    system: str

    # __post_init__ validates the user's input and sets up logz.io listener
    def __post_init__(self):
        if not self.__validate_input():
            return

        if self.logzio_listener != "":
            return

        if self.logzio_region_code == "" or self.logzio_region_code == "us":
            self.logzio_listener = "https://listener.logz.io:8071"
        else:
            self.logzio_listener = "https://listener-{}.logz.io:8071".format(self.logzio_region_code)

    class dom_is_completed(object):
        """
        An expectation for checking that the DOM elements load is complete.
        """

        def __init__(self):
            pass

        def __call__(self, driver):
            return self.__get_status_ready(driver)

        def __get_status_ready(self, driver):
            js_script = "return document.readyState"
            ready_response = driver.execute_script(js_script)
            return ready_response == 'complete'

    # monitor sets up and runs the web driver, gets relevant metrics and sends them to logz.io
    def monitor(self):
        driver = self.__get_driver()
        if driver:
            is_dom_complete = False
            try:
                driver.get(self.url)
                wait = WebDriverWait(driver, self.MAX_DOM_COMPLETE)
                check_dom = self.dom_is_completed()
                is_dom_complete = wait.until(check_dom)
            except exceptions.TimeoutException:
                self.__send_log("domComplete event didn't occur within the time limit")
            except Exception as e:
                self.__send_log("Error occurred while trying to load page: {}".format(e))
            finally:
                all_metrics = []
                # Whole DOM metric
                web_metrics = self.__get_page_metrics(driver, is_dom_complete)
                all_metrics.append(web_metrics)
                # Resource metrics
                resources = driver.execute_script("return window.performance.getEntriesByType('resource')")
                for r in resources:
                    resource_metric = self.__get_resource_metrics(driver, r)
                    if resource_metric:
                        all_metrics.append(resource_metric)

                if all_metrics:
                    for metric in all_metrics:
                        self.__send_metrics(metric)
                    self.__create_and_send_supervision_metric(len(all_metrics))
                    self.__send_log("Sending {} metrics documents".format(len(all_metrics)))
                driver.quit()

    # __validate_input validates the user input with the input_validator module
    def __validate_input(self):
        input_validator.is_valid_url(self.url)
        input_validator.is_valid_logzio_token(self.logs_token)
        input_validator.is_valid_logzio_token(self.metrics_token)
        input_validator.is_valid_logzio_region_code(self.logzio_region_code)
        input_validator.is_supported_system(self.system)
        input_validator.is_valid_system_region(self.system, self.region)
        input_validator.is_valid_function_name(self.function_name)
        return True

    # __get_driver sets up the headless chrome web driver
    def __get_driver(self):
        try:
            desired_capabilities = DesiredCapabilities.CHROME
            desired_capabilities['goog:loggingPrefs'] = {'browser': 'ALL', 'performance': 'ALL'}
            options = webdriver.ChromeOptions()
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
            if self.system != "none":
                options.binary_location = self.__get_chrome_binary_by_system()
            driver = webdriver.Chrome(desired_capabilities=desired_capabilities, options=options)
            return driver
        except exceptions.WebDriverException as e:
            self.__send_log("Error creating web driver. {}".format(e))
            return {}

    # __send_log sends log to your logz.io account
    def __send_log(self, message):
        timestamp = self.__format_timestamp(datetime.datetime.now(tz=datetime.timezone.utc))
        log = {"@timestamp": timestamp, "message": message, "type": "synthetic-monitoring",
               "lambda_function": self.function_name, "region": self.region,
               "url": self.url}
        self.__send_data(json.dumps(log), is_metrics=False)

    # __send_metrics sends metrics to your logz.io account
    def __send_metrics(self, metrics):
        try:
            self.__send_data(json.dumps(metrics))
        except Exception as e:
            self.__send_log("Error occurred while trying to send metrics. {}".format(e))

    # __send_data sends over HTTPS either a log or a metric to your logz.io account,
    # based on the token & is_metrics flag
    def __send_data(self, data, is_metrics=True):
        try:
            token = self.metrics_token if is_metrics else self.logs_token
            url = "{}/?token={}".format(self.logzio_listener, token)
            response = requests.post(url, data=data)
            if not response.ok:
                # TODO
                pass
        except Exception as e:
            # TODO
            pass

    # __get_page_metrics creates the web page metric
    def __get_page_metrics(self, driver, is_dom_complete):
        try:
            js_script_timestamp = "return window.performance.timing.navigationStart"
            timestamp = datetime.datetime.fromtimestamp(
                self.__ms_to_seconds(driver.execute_script(js_script_timestamp)),
                tz=datetime.timezone.utc)
            data = {"@timestamp": self.__format_timestamp(timestamp),
                    "type": "synthetic-monitoring",
                    "metrics": self.__create_metrics(driver, is_dom_complete)}
            dimensions = {"country": self.__get_country_code(), "region": self.region, "url": self.url}
            data["dimensions"] = dimensions
            return data
        except Exception as e:
            self.__send_log("Error occurred while getting page metrics: {}".format(e))
            return {}

    # __get_resource_metrics creates the resource metrics
    def __get_resource_metrics(self, driver, resource):
        try:
            js_script_timestamp = "return window.performance.timing.navigationStart"
            timestamp = datetime.datetime.fromtimestamp(
                self.__ms_to_seconds(driver.execute_script(js_script_timestamp)),
                tz=datetime.timezone.utc)
            data = {"@timestamp": self.__format_timestamp(timestamp),
                    "type": "synthetic-monitoring",
                    "metrics": self.__create_resource_metrics(resource)}
            dimensions = {"country": self.__get_country_code(), "region": self.region, "url": self.url,
                          "resource_name": resource["name"], "resource_type": resource['initiatorType']}
            data["dimensions"] = dimensions
            return data
        except Exception as e:
            self.__send_log("Error occurred while getting resource metrics: {}".format(e))
            return {}

    # __create_metrics gets data from the web driver's Timing API and calculates the metrics values for the page metric
    def __create_metrics(self, driver, is_dom_complete):
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
            status_code = self.__get_page_status_code(driver)
            if status_code:
                metrics["status_code"] = status_code
                if 200 <= status_code < 300:
                    metrics["up"] = self.SUCCESS
                elif 400 <= status_code < 600:
                    metrics["up"] = self.FAILURE
                    self.__send_log(
                        "Page {} returned status code {} for region {}".format(driver.current_url, status_code,
                                                                               self.region))
            return metrics
        except Exception as e:
            self.__send_log("Error creating page's metrics. {}".format(e))
            return {}

    # __create_resource_metrics calculates how much time it took for the resource to load
    def __create_resource_metrics(self, resource):
        try:
            metrics = {}
            fetch_start = resource['fetchStart']
            response_end = resource['responseEnd']
            metrics["time_to_complete.ms"] = response_end - fetch_start
            return metrics
        except Exception as e:
            self.__send_log("Error creating page's metrics. {}".format(e))
            return {}

    # __get_country_code converts the system's region to the matching country code, to appear in the metrics
    def __get_country_code(self):
        try:
            country_code = get_country_code_by_region_and_system(self.system, self.region)
            return country_code
        except ValueError:
            self.__send_log("{} region is not supported").format(self.region)
            pass

    # __get_page_status_code gets the page's status code (e.g. 200, 404, 500...)
    def __get_page_status_code(self, driver):
        try:
            performance_logs = driver.get_log('performance')
            status_code = self.__get_status(performance_logs)
            return int(status_code)
        except Exception as e:
            self.__send_log("Error occurred while getting performance logs: {}".format(e))
            return {}

    # __get_status extracts the page status code from its logs
    def __get_status(self, logs):
        for log in logs:
            if log['message']:
                d = json.loads(log['message'])
                try:
                    content_type = 'text/html' in d['message']['params']['response']['headers']['content-type']
                    response_received = d['message']['method'] == 'Network.responseReceived'
                    if content_type and response_received:
                        return d['message']['params']['response']['status']
                except:
                    # TODO
                    pass

    # __create_and_send_supervision_metric creates a metric with the number of metrics that were sent, and sends it to
    # your logz.io account
    def __create_and_send_supervision_metric(self, num_metrics):
        try:
            timestamp = self.__format_timestamp(datetime.datetime.now(tz=datetime.timezone.utc))
            data = {"@timestamp": timestamp,
                    "type": "synthetic-monitoring",
                    "metrics": {"metrics_sent": num_metrics}}
            dimensions = {"country": self.__get_country_code(), "region": self.region, "url": self.url}
            data["dimensions"] = dimensions
            self.__send_metrics(data)
        except Exception as e:
            self.__send_log("Error occured while creating supervision metric:\n{}".format(e))

    # __get_chrome_binary_by_system returns the path to the web driver binary, according to the system that's being used
    def __get_chrome_binary_by_system(self):
        if self.system == "aws":
            return "/opt/bin/chromium"

    # __format_timestamp formats a timestamp to logz.io's acceptable timestamp format 'yyyy-MM-ddTHH:mm:ss.SSSZ'
    def __format_timestamp(self, timestamp):
        return "{}Z".format(timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3])

    # __ms_to_seconds converts ms to seconds
    def __ms_to_seconds(self, ms):
        return ms / 1000
