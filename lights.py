from dataclasses import dataclass
import datetime
import json
import requests
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait


@dataclass()
class LightsMonitor(object):
    """
    Object for creating and sending web page metrics to logz.io
    """
    # class constants:
    SUCCESS = 1
    FAILURE = 0

    url: str
    metrics_token: str
    logs_token: str
    region: str
    logzio_region_code: str
    logzio_listener: str
    function_name: str
    protocol: str
    max_dom_complete: float  # seconds
    system: str

    def __post_init__(self):

        if self.protocol is None:
            self.protocol = "https"

        if self.logzio_listener != "":
            return

        if self.logzio_region_code == "" or self.logzio_region_code == "us":
            self.logzio_listener = "{}://listener.logz.io".format(self.protocol)
        else:
            self.logzio_listener = "{}://listener-{}.logz.io".format(self.protocol, self.logzio_region_code)

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

    def monitor(self):
        driver = self.__get_driver()
        if driver:
            is_dom_complete = False
            try:
                driver.get(self.url)
                wait = WebDriverWait(driver, self.max_dom_complete)
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
                    self.__send_log("Sending {} metrics documents".format(len(all_metrics)))
                driver.quit()

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
            options.binary_location = self.__get_chrome_binary_by_system()
            driver = webdriver.Chrome(desired_capabilities=desired_capabilities, options=options)
            return driver
        except Exception as e:
            self.__send_log("Error creating web driver. {}".format(e))
            return {}

    def __send_log(self, message):
        timestamp = self.__format_timestamp(datetime.datetime.now(tz=datetime.timezone.utc))
        log = {"@timestamp": timestamp, "message": message, "type": "synthetic-monitoring",
               "lambda_function": self.function_name, "region": self.region,
               "url": self.url}
        self.__send_data(json.dumps(log), is_metrics=False)

    def __send_metrics(self, metrics):
        try:
            self.__send_data(json.dumps(metrics))
        except Exception as e:
            self.__send_log("Error occurred while trying to send metrics. {}".format(e))

    def __send_data(self, data, is_metrics=True):
        try:
            port = self.__get_port_by_protocol()
            token = self.metrics_token if is_metrics else self.logs_token
            url = "{}:{}/?token={}".format(self.logzio_listener, port, token)
            response = requests.post(url, data=data)
            if not response.ok:
                # TODO
                pass
        except Exception as e:
            # TODO
            pass

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

    def __get_country_code(self):
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
            "sa-east-1": "BR",
            # Canada regions
            "ca-central-1": "CA"
        }
        try:
            country_code = country_codes_by_region[self.region]
            return country_code
        except Exception as e:
            self.__send_log("{} region is not supported").format(self.region)
            pass

    def __get_page_status_code(self, driver):
        try:
            performance_logs = driver.get_log('performance')
            status_code = self.__get_status(performance_logs)
            return int(status_code)
        except Exception as e:
            self.__send_log("Error occurred while getting performance logs: {}".format(e))
            return {}

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

    def __get_chrome_binary_by_system(self):
        if self.system == "aws":
            return "/opt/bin/chromium"

    def __format_timestamp(self, timestamp):
        return "{}Z".format(timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3])

    def __get_port_by_protocol(self):
        if self.protocol == "https":
            return "8071"
        else:
            return "8070"

    def __ms_to_seconds(self, ms):
        return ms / 1000
