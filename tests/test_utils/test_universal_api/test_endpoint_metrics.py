import unittest

import unify
from unify import Metrics


class TestEndpointMetrics(unittest.TestCase):

    def test_get_endpoint_metrics(self):
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
