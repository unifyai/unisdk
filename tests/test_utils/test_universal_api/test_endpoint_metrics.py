import unittest

import unify
from unify import Metrics


# noinspection PyBroadException
class CustomEndpointHandler:

    def __init__(self, endpoint_name, endpoint_url, key_name, key_value):
        self._endpoint_name = endpoint_name
        self._endpoint_url = endpoint_url
        self._key_name = key_name
        self._key_value = key_value

    def _cleanup(self):
        try:
            unify.delete_custom_api_key(self._key_name)
        except:
            pass
        try:
            unify.delete_custom_endpoint(self._endpoint_name)
        except:
            pass

    def __enter__(self):
        self._cleanup()
        unify.create_custom_api_key(self._key_name, self._key_value)
        unify.create_custom_endpoint(
            self._endpoint_name, self._endpoint_url, self._key_name
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()


class TestEndpointMetrics(unittest.TestCase):

    def setUp(self):
        self._endpoint_name = "my_endpoint@custom"
        self._endpoint_url = "test.com"
        self._key_name = "test_key"
        self._key_value = "4321"

        self._handler = CustomEndpointHandler(
            self._endpoint_name, self._endpoint_url, self._key_name, self._key_value
        )

    def test_get_public_endpoint_metrics(self):
        metrics = unify.get_endpoint_metrics("gpt-4o@openai")
        self.assertIsInstance(metrics, Metrics)
        self.assertTrue(hasattr(metrics, "time_to_first_token"))
        self.assertIsInstance(metrics.time_to_first_token, float)
        self.assertTrue(hasattr(metrics, "inter_token_latency"))
        self.assertIsInstance(metrics.inter_token_latency, float)
        self.assertTrue(hasattr(metrics, "input_cost"))
        self.assertIsInstance(metrics.input_cost, float)
        self.assertTrue(hasattr(metrics, "output_cost"))
        self.assertIsInstance(metrics.output_cost, float)
        self.assertTrue(hasattr(metrics, "measured_at"))
        self.assertIsInstance(metrics.measured_at, str)
        self.assertTrue(hasattr(metrics, "region"))
        self.assertIsInstance(metrics.region, str)
        self.assertTrue(hasattr(metrics, "seq_len"))
        self.assertIsInstance(metrics.seq_len, str)

    def test_log_endpoint_metric(self):
        with self._handler:
            unify.log_endpoint_metric(self._endpoint_name, "inter_token_latency", 1.23)
