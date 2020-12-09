import json
import os
import sys
import unittest
import requests_mock
import chromedriver_binary
sys.path.append("../aws")
import lambda_function


class TestAWS(unittest.TestCase):
    TEST_EVENT = {"some": "event"}
    TEST_CONTEXT = "context"
    TEST_LOGZIO_LISTENER = "https://example.com"

    def setUp(self):
        os.environ["LOGZIO_METRICS_TOKEN"] = "metricsLogzioTokenlogzioTokenLog"
        os.environ["LOGZIO_LOGS_TOKEN"] = "logsLogzioTokenlogzioTokenLogzio"
        os.environ["URL"] = "https://example.com,http://example.com"
        os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "test-func"
        os.environ["LOGZIO_REGION"] = "us"
        os.environ["AWS_REGION"] = "us-east-1"
        os.environ["SYSTEM"] = "none"

    # test_aws tests that the
    def test_aws(self):
        try:
            lambda_function.lambda_handler(self.TEST_EVENT, self.TEST_CONTEXT)
        except Exception as e:
            self.fail("lambda_handler raised an exception with valid input:\n{}".format(e))

    def test_invalid_logzio_token(self):
        invalid_tokens = ['34234786471271498130478163476257',
                          'acnDFejkjdfmksd3fdkDSslfjdEdjkdj',
                          'ahjksfhgishfgnsfjnvjgksfhgjhsfsw',
                          'DMKDNFKSJDHFKNSDMNVKSDNFLJKSKHGA',
                          'dkmsdjWEGRSFGskldsdDmfSDFksfkDs',
                          '']

        for token in invalid_tokens:
            with self.assertRaises(ValueError):
                os.environ["LOGZIO_METRICS_TOKEN"] = token
                lambda_function.lambda_handler(self.TEST_EVENT, self.TEST_CONTEXT)

        invalid_token_types = [None, 3]
        for token in invalid_token_types:
            with self.assertRaises(TypeError):
                os.environ["LOGZIO_METRICS_TOKEN"] = token
                lambda_function.lambda_handler(self.TEST_EVENT, self.TEST_CONTEXT)

    def test_invalid_urls(self):
        invalid_urls = ["https://wwww.example.com;http://www.example.com", "just.a.string"]

        for url in invalid_urls:
            with self.assertRaises(ValueError):
                os.environ["URL"] = url
                lambda_function.lambda_handler(self.TEST_EVENT, self.TEST_CONTEXT)

        invalid_url_types = [None, 4]
        for url in invalid_url_types:
            with self.assertRaises(TypeError):
                os.environ["URL"] = url
                lambda_function.lambda_handler(self.TEST_EVENT, self.TEST_CONTEXT)

    def test_invalid_logzio_region_code(self):
        invalid_regions = ["euu", "ab", "22"]
        for region in invalid_regions:
            with self.assertRaises(ValueError):
                os.environ["LOGZIO_REGION"] = region
                lambda_function.lambda_handler(self.TEST_EVENT, self.TEST_CONTEXT)

        invalid_regions_types = [2.5, {"region": "eu"}]
        for region in invalid_regions_types:
            with self.assertRaises(TypeError):
                os.environ["LOGZIO_REGION"] = region
                lambda_function.lambda_handler(self.TEST_EVENT, self.TEST_CONTEXT)

    def test_invalid_function_name(self):
        invalid_function_types = [1, 1.1, {"func": "test"}]
        for func_name in invalid_function_types:
            with self.assertRaises(TypeError):
                os.environ["AWS_LAMBDA_FUNCTION_NAME"] = func_name
                lambda_function.lambda_handler(self.TEST_EVENT, self.TEST_CONTEXT)

    def test_invalid_system(self):
        invalid_systems = ["aaa", "1e2"]
        for system in invalid_systems:
            with self.assertRaises(ValueError):
                os.environ["SYSTEM"] = system
                lambda_function.lambda_handler(self.TEST_EVENT, self.TEST_CONTEXT)

        invalid_system_types = [1, 1.1, {"system": "test"}, None]
        for system in invalid_system_types:
            with self.assertRaises(TypeError):
                os.environ["SYSTEM"] = system
                lambda_function.lambda_handler(self.TEST_EVENT, self.TEST_CONTEXT)

    def test_request(self):
        with requests_mock.Mocker() as m:
            os.environ["URL"] = "https://example.com"
            m.post("{}/?token={}".format(self.TEST_LOGZIO_LISTENER, os.environ["LOGZIO_METRICS_TOKEN"]))
            lambda_function.lambda_handler(self.TEST_EVENT, self.TEST_CONTEXT)
            self.assertGreater(len(m.request_history), 0)
            self.assertIn("metrics", json.loads(m.request_history[0].text))
