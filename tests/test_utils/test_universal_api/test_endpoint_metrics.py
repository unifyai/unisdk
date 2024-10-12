import unittest

import unify
from unify import Metrics


class TestEndpointMetrics(unittest.TestCase):

    def test_get_endpoint_metrics(self):
        metrics = unify.get_endpoint_metrics("gpt-4o@openai")
        self.assertIsInstance(metrics, Metrics)
        self.assertIn("time_to_first_token", metrics.model_fields)
        self.assertIn("inter_token_latency", metrics.model_fields)
        self.assertIn("input_cost", metrics.model_fields)
        self.assertIn("output_cost", metrics.model_fields)
        self.assertIn("measured_at", metrics.model_fields)

    def test_log_endpoint_metric(self):
        metrics = unify.log_endpoint("gpt-4o@openai")
