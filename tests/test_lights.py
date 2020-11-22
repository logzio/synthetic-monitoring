from unittest import TestCase
import sys

sys.path.append('..')
from lights import LightsMonitor


class TestLightS(TestCase):
    TEST_URL = "https://example.com"
    TEST_TOKEN = "someLogzioTokenlogzioTokenLogzio"
    TEST_LOGZIO_REGION_CODE = "us"
    TEST_LOGZIO_LISTENER = "https://example.com/"
    TEST_AWS_REGION = "us-east-1"
    TEST_FUNCTION_NAME = "test-func"
    TEST_MAX_DOM_COMPLETE = 7.0
    TEST_SYSTEM = "none"

    # Tests monitor func is working when all inputs are valid, with logzio region code
    def test_monitor(self):
        try:
            lightS = LightsMonitor(url=self.TEST_URL,
                                   logs_token=self.TEST_TOKEN,
                                   metrics_token=self.TEST_TOKEN,
                                   logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                   logzio_listener="",
                                   region="",
                                   function_name=self.TEST_FUNCTION_NAME,
                                   max_dom_complete=self.TEST_MAX_DOM_COMPLETE,
                                   system="none")
            lightS.monitor()
        except Exception as e:
            self.fail("lightS raised an exception with valid input:\n{}".format(e))

    def test_monitor_invalid_url(self):
        invalid_urls = ["just.a.string", ""]
        for url in invalid_urls:
            with self.assertRaises(ValueError):
                lights = LightsMonitor(url=url,
                                       logs_token=self.TEST_TOKEN,
                                       metrics_token=self.TEST_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       max_dom_complete=self.TEST_MAX_DOM_COMPLETE,
                                       system="none")

        invalid_url_types = [None, 4]
        for url in invalid_url_types:
            with self.assertRaises(TypeError):
                lights = LightsMonitor(url=url,
                                       logs_token=self.TEST_TOKEN,
                                       metrics_token=self.TEST_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       max_dom_complete=self.TEST_MAX_DOM_COMPLETE,
                                       system="none")

    def test_monitor_invalid_tokens(self):
        invalid_tokens = ['34234786471271498130478163476257',
                          'acnDFejkjdfmksd3fdkDSslfjdEdjkdj',
                          'ahjksfhgishfgnsfjnvjgksfhgjhsfsw',
                          'DMKDNFKSJDHFKNSDMNVKSDNFLJKSKHGA',
                          'dkmsdjWEGRSFGskldsdDmfSDFksfkDs',
                          '']

        for token in invalid_tokens:
            with self.assertRaises(TypeError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=token,
                                       metrics_token=self.TEST_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       max_dom_complete=self.TEST_MAX_DOM_COMPLETE,
                                       system="none")

        invalid_token_types = [None, 3]
        for token in invalid_token_types:
            with self.assertRaises(ValueError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=token,
                                       metrics_token=self.TEST_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       max_dom_complete=self.TEST_MAX_DOM_COMPLETE,
                                       system="none")

    def test_monitor_no_logzio_region_code_or_listener(self):
        with self.assertRaises(ValueError):
            lightS = LightsMonitor(url=self.TEST_URL,
                                   logs_token=self.TEST_TOKEN,
                                   metrics_token=self.TEST_TOKEN,
                                   logzio_region_code="",
                                   logzio_listener="",
                                   region="",
                                   function_name=self.TEST_FUNCTION_NAME,
                                   max_dom_complete=self.TEST_MAX_DOM_COMPLETE,
                                   system="none")

    def test_monitor_invalid_logzio_region_code(self):
        invalid_regions = ["euu", "ab", "22", ""]
        for region in invalid_regions:
            with self.assertRaises(ValueError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=self.TEST_TOKEN,
                                       metrics_token=self.TEST_TOKEN,
                                       logzio_region_code=region,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       max_dom_complete=self.TEST_MAX_DOM_COMPLETE,
                                       system="none")

        invalid_regions_types = [2.5, {"region": "eu"}]
        for region in invalid_regions_types:
            with self.assertRaises(TypeError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=self.TEST_TOKEN,
                                       metrics_token=self.TEST_TOKEN,
                                       logzio_region_code=region,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       max_dom_complete=self.TEST_MAX_DOM_COMPLETE,
                                       system="none")

    def test_monitor_invalid_function_name(self):
        invalid_function_types = [1, 1.1, {"func": "test"}]
        for func_name in invalid_function_types:
            with self.assertRaises(TypeError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=self.TEST_TOKEN,
                                       metrics_token=self.TEST_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=func_name,
                                       max_dom_complete=self.TEST_MAX_DOM_COMPLETE,
                                       system="none")

    def test_monitor_invalid_max_dom_complete(self):
        invalid_dom_complete_vals = [0.0, -1.0, 0, -2, "0", "-3"]
        for max_val in invalid_dom_complete_vals:
            with self.assertRaises(ValueError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=self.TEST_TOKEN,
                                       metrics_token=self.TEST_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       max_dom_complete=max_val,
                                       system="none")

        invalid_dom_complete_types = ["str", {"max": "3"}]
        for max_val in invalid_dom_complete_types:
            with self.assertRaises(TypeError):
                lightS = LightsMonitor(url=self.TEST_URL,
                                       logs_token=self.TEST_TOKEN,
                                       metrics_token=self.TEST_TOKEN,
                                       logzio_region_code=self.TEST_LOGZIO_REGION_CODE,
                                       logzio_listener="",
                                       region="",
                                       function_name=self.TEST_FUNCTION_NAME,
                                       max_dom_complete=max_val,
                                       system="none")