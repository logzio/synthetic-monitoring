from unittest import TestCase
import json
import requests_mock
import sys
sys.path.append('..')
from lights import LightsMonitor


class TestLightS(TestCase):
    TEST_URL = "https://example.com"
    TEST_LOGS_TOKEN = "logsLogzioTokenlogzioTokenLogzio"
    TEST_METRICS_TOKEN = "metricsLogzioTokenlogzioTokenLog"
    TEST_LOGZIO_REGION_CODE = "us"
    TEST_LOGZIO_LISTENER = "https://example.com/"
    TEST_FUNCTION_NAME = "test-func"
    TEST_SYSTEM = "none"

    # Tests monitor func is working when all inputs are valid, with logzio region code
    def test_monitor(self):
        try:
            lightS = LightsMonitor(url=self.TEST_URL,
                                   logs_token=self.TEST_LOGS_TOKEN,
                                   metrics_token=self.TEST_METRICS_TOKEN,
                                   logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                   logzio_listener="",
                                   region="",
                                   function_name=self.TEST_FUNCTION_NAME,
                                   system="none")
            lightS.monitor()
        except Exception as e:
            self.fail("lightS raised an exception with valid input:\n{}".format(e))

    # Tests monitor func raises ValueError and TypeError for invalid urls
    def test_monitor_invalid_url(self):
        invalid_urls = ["just.a.string", "", "1", "aa:aa"]
        for url in invalid_urls:
            with self.assertRaises(ValueError):
                lights = LightsMonitor(url=url,
                                       logs_token=self.TEST_LOGS_TOKEN,
                                       metrics_token=self.TEST_METRICS_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       system="none")

        invalid_url_types = [None, 4]
        for url in invalid_url_types:
            with self.assertRaises(TypeError):
                lights = LightsMonitor(url=url,
                                       logs_token=self.TEST_LOGS_TOKEN,
                                       metrics_token=self.TEST_METRICS_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       system="none")

    # Tests monitor func raises ValueError and TypeError for invalid tokens
    def test_monitor_invalid_tokens(self):
        invalid_tokens = ['34234786471271498130478163476257',
                          'acnDFejkjdfmksd3fdkDSslfjdEdjkdj',
                          'ahjksfhgishfgnsfjnvjgksfhgjhsfsw',
                          'DMKDNFKSJDHFKNSDMNVKSDNFLJKSKHGA',
                          'dkmsdjWEGRSFGskldsdDmfSDFksfkDs',
                          '']

        for token in invalid_tokens:
            with self.assertRaises(ValueError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=token,
                                       metrics_token=self.TEST_METRICS_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       system="none")

        invalid_token_types = [None, 3]
        for token in invalid_token_types:
            with self.assertRaises(TypeError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=token,
                                       metrics_token=self.TEST_METRICS_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       system="none")

    # Tests monitor func raises ValueError when no logzio region code or listener are inserted
    def test_monitor_no_logzio_region_code_or_listener(self):
        with self.assertRaises(ValueError):
            lightS = LightsMonitor(url=self.TEST_URL,
                                   logs_token=self.TEST_LOGS_TOKEN,
                                   metrics_token=self.TEST_METRICS_TOKEN,
                                   logzio_region_code="",
                                   logzio_listener="",
                                   region="",
                                   function_name=self.TEST_FUNCTION_NAME,
                                   system="none")

    # Tests monitor func raises ValueError and TypeError for invalid logzio region code
    def test_monitor_invalid_logzio_region_code(self):
        invalid_regions = ["euu", "ab", "22", ""]
        for region in invalid_regions:
            with self.assertRaises(ValueError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=self.TEST_LOGS_TOKEN,
                                       metrics_token=self.TEST_METRICS_TOKEN,
                                       logzio_region_code=region,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       system="none")

        invalid_regions_types = [2.5, {"region": "eu"}]
        for region in invalid_regions_types:
            with self.assertRaises(TypeError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=self.TEST_LOGS_TOKEN,
                                       metrics_token=self.TEST_METRICS_TOKEN,
                                       logzio_region_code=region,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       system="none")

    # Tests monitor func raises TypeError for invalid function name
    def test_monitor_invalid_function_name(self):
        invalid_function_types = [1, 1.1, {"func": "test"}]
        for func_name in invalid_function_types:
            with self.assertRaises(TypeError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=self.TEST_LOGS_TOKEN,
                                       metrics_token=self.TEST_METRICS_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=func_name,
                                       system="none")

    # Tests monitor func raises ValueError and TypeError for invalid system
    def test_monitor_invalid_system(self):
        invalid_systems = ["aaa", "1e2"]
        for system in invalid_systems:
            with self.assertRaises(ValueError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=self.TEST_LOGS_TOKEN,
                                       metrics_token=self.TEST_METRICS_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       system=system)

        invalid_system_types = [1, 1.1, {"system": "test"}, None]
        for system in invalid_system_types:
            with self.assertRaises(TypeError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=self.TEST_LOGS_TOKEN,
                                       metrics_token=self.TEST_METRICS_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       system=system)

    # Tests the requests sent from the monitor
    def test_monitor_request(self):
        with requests_mock.Mocker() as m:
            m.post("{}/?token={}".format(self.TEST_LOGZIO_LISTENER, self.TEST_METRICS_TOKEN))
            lightS = LightsMonitor(url=self.TEST_URL,
                                   logs_token=self.TEST_LOGS_TOKEN,
                                   metrics_token=self.TEST_METRICS_TOKEN,
                                   logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                   logzio_listener=self.TEST_LOGZIO_LISTENER,
                                   region="",
                                   function_name=self.TEST_FUNCTION_NAME,
                                   system="none")
            lightS.monitor()
            self.assertGreater(len(m.request_history), 0)
            self.assertIn("metrics", json.loads(m.request_history[0].text))
