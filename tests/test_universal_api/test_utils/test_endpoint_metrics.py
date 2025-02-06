import time
from datetime import datetime, timezone

import unify
from unify import Metrics


# noinspection PyBroadException
class CustomEndpointHandler:
    def __init__(self, ep_name, ep_url, ky_name, ky_value):
        self.endpoint_name = ep_name
        self._endpoint_url = ep_url
        self._key_name = ky_name
        self._key_value = ky_value

    def _cleanup(self):
        try:
            unify.delete_endpoint_metrics(self.endpoint_name)
        except:
            pass
        try:
            unify.delete_custom_endpoint(self.endpoint_name)
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
            name=self.endpoint_name,
            url=self._endpoint_url,
            key_name=self._key_name,
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()


endpoint_name = "my_endpoint@custom"
endpoint_url = "test.com"
key_name = "test_key"
key_value = "4321"
handler = CustomEndpointHandler(
    endpoint_name,
    endpoint_url,
    key_name,
    key_value,
)


def test_get_public_endpoint_metrics():
    metrics = unify.get_endpoint_metrics("gpt-4o@openai")
    assert isinstance(metrics, list)
    assert len(metrics) == 1
    metrics = metrics[0]
    assert isinstance(metrics, Metrics)
    assert hasattr(metrics, "ttft")
    assert isinstance(metrics.ttft, float)
    assert hasattr(metrics, "itl")
    assert isinstance(metrics.itl, float)
    assert hasattr(metrics, "input_cost")
    assert isinstance(metrics.input_cost, float)
    assert hasattr(metrics, "output_cost")
    assert isinstance(metrics.output_cost, float)
    assert hasattr(metrics, "measured_at")
    assert isinstance(metrics.measured_at, str)


def test_client_metric_properties():
    client = unify.Unify("gpt-4o@openai", cache=True)
    assert isinstance(client.input_cost, float)
    assert isinstance(client.output_cost, float)
    assert isinstance(client.ttft, float)
    assert isinstance(client.itl, float)
    client = unify.MultiUnify(
        ["gpt-4o@openai", "claude-3-haiku@anthropic"],
        cache=True,
    )
    assert isinstance(client.input_cost, dict)
    assert isinstance(client.input_cost["gpt-4o@openai"], float)
    assert isinstance(client.input_cost["claude-3-haiku@anthropic"], float)
    assert isinstance(client.output_cost, dict)
    assert isinstance(client.output_cost["gpt-4o@openai"], float)
    assert isinstance(client.output_cost["claude-3-haiku@anthropic"], float)
    assert isinstance(client.ttft, dict)
    assert isinstance(client.ttft["gpt-4o@openai"], float)
    assert isinstance(client.ttft["claude-3-haiku@anthropic"], float)
    assert isinstance(client.itl, dict)
    assert isinstance(client.itl["gpt-4o@openai"], float)
    assert isinstance(client.itl["claude-3-haiku@anthropic"], float)


def test_log_endpoint_metric():
    with handler:
        unify.log_endpoint_metric(
            endpoint_name,
            metric_name="itl",
            value=1.23,
        )


def test_log_and_get_endpoint_metric():
    with handler:
        now = datetime.now(timezone.utc)
        unify.log_endpoint_metric(
            endpoint_name,
            metric_name="itl",
            value=1.23,
        )
        metrics = unify.get_endpoint_metrics(endpoint_name, start_time=now)
        assert isinstance(metrics, list)
        assert len(metrics) == 1
        metrics = metrics[0]
        assert hasattr(metrics, "itl")
        assert isinstance(metrics.itl, float)
        assert metrics.itl == 1.23


def test_log_and_get_endpoint_metric_with_time_windows():
    with handler:
        t0 = datetime.now(timezone.utc)
        unify.log_endpoint_metric(
            endpoint_name,
            metric_name="itl",
            value=1.23,
        )
        unify.log_endpoint_metric(
            endpoint_name,
            metric_name="ttft",
            value=4.56,
        )
        time.sleep(0.5)
        t1 = datetime.now(timezone.utc)
        unify.log_endpoint_metric(
            endpoint_name,
            metric_name="itl",
            value=7.89,
        )
        all_metrics = unify.get_endpoint_metrics(endpoint_name, start_time=t0)
        # two log events detected, due to double itl logging
        assert len(all_metrics) == 2
        # Data all accumulates at the latest entry (top of the stack)
        assert isinstance(all_metrics[0].itl, float)
        assert all_metrics[0].ttft is None
        assert isinstance(all_metrics[1].itl, float)
        assert isinstance(all_metrics[1].ttft, float)
        assert all_metrics[0].itl == 1.23
        assert all_metrics[1].ttft == 4.56
        assert all_metrics[1].itl == 7.89
        # The original two logs are not retrieved
        limited_metrics = unify.get_endpoint_metrics(
            endpoint_name,
            start_time=t1,
        )
        assert len(limited_metrics) == 1
        assert limited_metrics[0].ttft is None
        assert isinstance(limited_metrics[0].itl, float)
        assert limited_metrics[0].itl == 7.89
        # The ttft is now retrieved due to 'latest' mode
        latest_metrics = unify.get_endpoint_metrics(endpoint_name)
        assert len(latest_metrics) == 1
        assert isinstance(latest_metrics[0].ttft, float)
        assert isinstance(latest_metrics[0].itl, float)
        assert latest_metrics[0].ttft == 4.56
        assert latest_metrics[0].itl == 7.89


def test_delete_all_metrics_for_endpoint():
    with handler:
        # log metric
        unify.log_endpoint_metric(
            endpoint_name,
            metric_name="itl",
            value=1.23,
        )
        # verify it exists
        metrics = unify.get_endpoint_metrics(endpoint_name)
        assert isinstance(metrics, list)
        assert len(metrics) == 1
        # delete it
        unify.delete_endpoint_metrics(endpoint_name)
        # verify it no longer exists
        metrics = unify.get_endpoint_metrics(endpoint_name)
        assert isinstance(metrics, list)
        assert len(metrics) == 0


def test_delete_some_metrics_for_endpoint():
    with handler:
        # log metrics at t0
        t0 = datetime.now(timezone.utc)
        unify.log_endpoint_metric(
            endpoint_name,
            metric_name="itl",
            value=1.23,
        )
        unify.log_endpoint_metric(
            endpoint_name,
            metric_name="ttft",
            value=4.56,
        )
        time.sleep(0.5)
        # log metric at t1
        unify.log_endpoint_metric(
            endpoint_name,
            metric_name="itl",
            value=7.89,
        )
        # verify both exist
        metrics = unify.get_endpoint_metrics(endpoint_name, start_time=t0)
        assert len(metrics) == 2
        # delete the first itl entry
        unify.delete_endpoint_metrics(
            endpoint_name,
            timestamps=metrics[0].measured_at["itl"],
        )
        # verify only the latest entry exists, with both itl and ttft
        metrics = unify.get_endpoint_metrics(endpoint_name, start_time=t0)
        assert len(metrics) == 1
        assert isinstance(metrics[0].itl, float)
        assert isinstance(metrics[0].ttft, float)
        # delete the ttft entry
        unify.delete_endpoint_metrics(
            endpoint_name,
            timestamps=metrics[0].measured_at["ttft"],
        )
        # verify only the latest entry exists, with only the itl
        metrics = unify.get_endpoint_metrics(endpoint_name, start_time=t0)
        assert len(metrics) == 1
        assert isinstance(metrics[0].itl, float)
        assert metrics[0].ttft is None
        # delete the final itl entry
        unify.delete_endpoint_metrics(
            endpoint_name,
            timestamps=metrics[0].measured_at["itl"],
        )
        # verify no metrics exist
        metrics = unify.get_endpoint_metrics(endpoint_name, start_time=t0)
        assert len(metrics) == 0


if __name__ == "__main__":
    pass
