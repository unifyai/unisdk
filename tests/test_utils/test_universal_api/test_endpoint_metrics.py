import time
import unittest
from datetime import datetime, timezone

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
            unify.delete_endpoint_metrics(self._endpoint_name)
        except:
            pass
        try:
            unify.delete_custom_endpoint(self._endpoint_name)
        except:
            pass
        try:
            unify.delete_custom_api_key(self._key_name)
        except:
            pass

    def __enter__(self):
        self._cleanup()
        unify.create_custom_api_key(self._key_name, self._key_value)
        unify.create_custom_endpoint(
            self._endpoint_name,
            self._endpoint_url,
            self._key_name,
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
            self._endpoint_name,
            self._endpoint_url,
            self._key_name,
            self._key_value,
        )

    def test_get_public_endpoint_metrics(self):
        metrics = unify.get_endpoint_metrics("gpt-4o@openai")
        self.assertIsInstance(metrics, list)
        self.assertEqual(len(metrics), 1)
        metrics = metrics[0]
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

    def test_client_metric_properties(self):
        client = unify.Unify("gpt-4o@openai")
        assert isinstance(client.input_cost, float)
        assert isinstance(client.output_cost, float)
        assert isinstance(client.time_to_first_token, float)
        assert isinstance(client.inter_token_latency, float)
        client = unify.MultiLLM(["gpt-4o@openai", "claude-3-haiku@anthropic"])
        assert isinstance(client.input_cost, dict)
        assert isinstance(client.input_cost["gpt-4o@openai"], float)
        assert isinstance(client.input_cost["claude-3-haiku@anthropic"], float)
        assert isinstance(client.output_cost, dict)
        assert isinstance(client.output_cost["gpt-4o@openai"], float)
        assert isinstance(client.output_cost["claude-3-haiku@anthropic"], float)
        assert isinstance(client.time_to_first_token, dict)
        assert isinstance(client.time_to_first_token["gpt-4o@openai"], float)
        assert isinstance(client.time_to_first_token["claude-3-haiku@anthropic"], float)
        assert isinstance(client.inter_token_latency, dict)
        assert isinstance(client.inter_token_latency["gpt-4o@openai"], float)
        assert isinstance(client.inter_token_latency["claude-3-haiku@anthropic"], float)

    def test_log_endpoint_metric(self):
        with self._handler:
            unify.log_endpoint_metric(self._endpoint_name, "inter_token_latency", 1.23)

    def test_log_and_get_endpoint_metric(self):
        with self._handler:
            now = datetime.now(timezone.utc)
            unify.log_endpoint_metric(self._endpoint_name, "inter_token_latency", 1.23)
            metrics = unify.get_endpoint_metrics(self._endpoint_name, start_time=now)
            self.assertIsInstance(metrics, list)
            self.assertEqual(len(metrics), 1)
            metrics = metrics[0]
            self.assertTrue(hasattr(metrics, "inter_token_latency"))
            self.assertIsInstance(metrics.inter_token_latency, float)
            self.assertEqual(metrics.inter_token_latency, 1.23)

    def test_log_and_get_endpoint_metric_with_time_windows(self):
        with self._handler:
            t0 = datetime.now(timezone.utc)
            unify.log_endpoint_metric(self._endpoint_name, "inter_token_latency", 1.23)
            unify.log_endpoint_metric(self._endpoint_name, "time_to_first_token", 4.56)
            time.sleep(0.5)
            t1 = datetime.now(timezone.utc)
            unify.log_endpoint_metric(self._endpoint_name, "inter_token_latency", 7.89)
            all_metrics = unify.get_endpoint_metrics(self._endpoint_name, start_time=t0)
            # two log events detected, due to double inter_token_latency logging
            self.assertEqual(len(all_metrics), 2)
            # Data all accumulates at the latest entry (top of the stack)
            self.assertIsInstance(all_metrics[0].inter_token_latency, float)
            self.assertIs(all_metrics[0].time_to_first_token, None)
            self.assertIsInstance(all_metrics[1].inter_token_latency, float)
            self.assertIsInstance(all_metrics[1].time_to_first_token, float)
            self.assertEqual(all_metrics[0].inter_token_latency, 1.23)
            self.assertEqual(all_metrics[1].time_to_first_token, 4.56)
            self.assertEqual(all_metrics[1].inter_token_latency, 7.89)
            # The original two logs are not retrieved
            limited_metrics = unify.get_endpoint_metrics(
                self._endpoint_name,
                start_time=t1,
            )
            self.assertEqual(len(limited_metrics), 1)
            self.assertIs(limited_metrics[0].time_to_first_token, None)
            self.assertIsInstance(limited_metrics[0].inter_token_latency, float)
            self.assertEqual(limited_metrics[0].inter_token_latency, 7.89)
            # The time_to_first_token is now retrieved due to 'latest' mode
            latest_metrics = unify.get_endpoint_metrics(self._endpoint_name)
            self.assertEqual(len(latest_metrics), 1)
            self.assertIsInstance(latest_metrics[0].time_to_first_token, float)
            self.assertIsInstance(latest_metrics[0].inter_token_latency, float)
            self.assertEqual(latest_metrics[0].time_to_first_token, 4.56)
            self.assertEqual(latest_metrics[0].inter_token_latency, 7.89)

    def test_delete_all_metrics_for_endpoint(self):
        with self._handler:
            # log metric
            unify.log_endpoint_metric(self._endpoint_name, "inter_token_latency", 1.23)
            # verify it exists
            metrics = unify.get_endpoint_metrics(self._endpoint_name)
            self.assertIsInstance(metrics, list)
            self.assertEqual(len(metrics), 1)
            # delete it
            unify.delete_endpoint_metrics(self._endpoint_name)
            # verify it no longer exists
            metrics = unify.get_endpoint_metrics(self._endpoint_name)
            self.assertIsInstance(metrics, list)
            self.assertEqual(len(metrics), 0)

    def test_delete_some_metrics_for_endpoint(self):
        with self._handler:
            # log metrics at t0
            t0 = datetime.now(timezone.utc)
            unify.log_endpoint_metric(self._endpoint_name, "inter_token_latency", 1.23)
            unify.log_endpoint_metric(self._endpoint_name, "time_to_first_token", 4.56)
            time.sleep(0.5)
            # log metric at t1
            t1 = datetime.now(timezone.utc)
            unify.log_endpoint_metric(self._endpoint_name, "inter_token_latency", 7.89)
            # verify both exist
            metrics = unify.get_endpoint_metrics(self._endpoint_name, start_time=t0)
            self.assertEqual(len(metrics), 2)
            # delete the first itl entry
            unify.delete_endpoint_metrics(
                self._endpoint_name,
                metrics[0].measured_at["inter_token_latency"],
            )
            # verify only the latest entry exists, with both itl and ttft
            metrics = unify.get_endpoint_metrics(self._endpoint_name, start_time=t0)
            self.assertEqual(len(metrics), 1)
            self.assertIsInstance(metrics[0].inter_token_latency, float)
            self.assertIsInstance(metrics[0].time_to_first_token, float)
            # delete the ttft entry
            unify.delete_endpoint_metrics(
                self._endpoint_name,
                metrics[0].measured_at["time_to_first_token"],
            )
            # verify only the latest entry exists, with only the itl
            metrics = unify.get_endpoint_metrics(self._endpoint_name, start_time=t0)
            self.assertEqual(len(metrics), 1)
            self.assertIsInstance(metrics[0].inter_token_latency, float)
            self.assertIs(metrics[0].time_to_first_token, None)
            # delete the final itl entry
            unify.delete_endpoint_metrics(
                self._endpoint_name,
                metrics[0].measured_at["inter_token_latency"],
            )
            # verify no metrics exist
            metrics = unify.get_endpoint_metrics(self._endpoint_name, start_time=t0)
            self.assertEqual(len(metrics), 0)
