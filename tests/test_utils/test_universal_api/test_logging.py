import unittest
from datetime import datetime, timedelta, timezone

import unify


# noinspection PyBroadException
class LoggingHandler:

    def __init__(self, key_name, endpoint_names):
        self._key_name = key_name
        self._endpoint_names = endpoint_names

    def _handle(self):
        try:
            unify.delete_custom_api_key(self._key_name)
        except:
            pass
        for endpoint_name in self._endpoint_names:
            try:
                unify.delete_custom_endpoint(endpoint_name)
            except:
                pass

    def __enter__(self):
        self._handle()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._handle()


class TestLogQuery(unittest.TestCase):

    def setUp(self):
        self.start_time = datetime.now(timezone.utc)
        self.tag = "test_tag"
        self.data = {
            "endpoint": "local_model_test@external",
            "query_body": {
                "messages": [
                    {"role": "system", "content": "You are an useful assistant"},
                    {"role": "user", "content": "Explain who Newton was."},
                ],
                "model": "llama-3-8b-chat@aws-bedrock",
                "max_tokens": 100,
                "temperature": 0.5,
            },
            "response_body": {
                "model": "meta.llama3-8b-instruct-v1:0",
                "created": 1725396241,
                "id": "chatcmpl-92d3b36e-7b64-4ae8-8102-9b7e3f5dd30f",
                "object": "chat.completion",
                "usage": {
                    "completion_tokens": 100,
                    "prompt_tokens": 44,
                    "total_tokens": 144,
                },
                "choices": [
                    {
                        "finish_reason": "stop",
                        "index": 0,
                        "message": {
                            "content": "Sir Isaac Newton was an English mathematician, "
                            "physicist, and astronomer who lived from 1643 "
                            "to 1727.\\n\\nHe is widely recognized as one "
                            "of the most influential scientists in history, "
                            "and his work laid the foundation for the "
                            "Scientific Revolution of the 17th century."
                            "\\n\\nNewton's most famous achievement is his "
                            "theory of universal gravitation, which he "
                            "presented in his groundbreaking book "
                            '"Philosophi\\u00e6 Naturalis Principia '
                            'Mathematica" in 1687.',
                            "role": "assistant",
                        },
                    },
                ],
            },
            "timestamp": (self.start_time + timedelta(seconds=0.01)),
            "tags": [self.tag],
        }

    def test_log_query_manually(self):
        result = unify.log_query(**self.data)
        self.assertIsInstance(result, dict)
        self.assertIn("info", result)
        self.assertEqual(result["info"], "Query logged successfully")

    def test_log_query_via_chat_completion(self):
        client = unify.Unify("gpt-4o@openai")
        response = client.generate(
            "hello",
            log_query_body=True,
            log_response_body=True,
        )
        self.assertIsInstance(response, str)

    def test_get_queries_from_manual(self):
        unify.log_query(**self.data)
        history = unify.get_queries(
            endpoints="local_model_test@external",
            start_time=self.start_time,
        )
        self.assertEqual(len(history), 1)
        history = unify.get_queries(
            endpoints="local_model_test@external",
            start_time=datetime.now(timezone.utc) + timedelta(seconds=1),
        )
        self.assertEqual(len(history), 0)

    def test_get_queries_from_chat_completion(self):
        unify.Unify("gpt-4o@openai").generate(
            "hello",
            log_query_body=True,
            log_response_body=True,
        )
        history = unify.get_queries(
            endpoints="gpt-4o@openai",
            start_time=self.start_time,
        )
        self.assertEqual(len(history), 1)
        history = unify.get_queries(
            endpoints="gpt-4o@openai",
            start_time=datetime.now(timezone.utc) + timedelta(seconds=1),
        )
        self.assertEqual(len(history), 0)

    def test_get_query_failures(self):
        client = unify.Unify("gpt-4o@openai")
        client.generate(
            "hello",
            log_query_body=True,
            log_response_body=True,
        )
        with self.assertRaises(Exception):
            client.generate(
                "hello",
                log_query_body=True,
                log_response_body=True,
                drop_params=False,
                invalid_arg="invalid_value",
            )

        # inside logged timeframe
        history_w_both = unify.get_queries(
            endpoints="gpt-4o@openai",
            start_time=self.start_time,
            failures=True,
        )
        self.assertEqual(len(history_w_both), 2)
        history_only_failures = unify.get_queries(
            endpoints="gpt-4o@openai",
            start_time=self.start_time,
            failures="only",
        )
        self.assertEqual(len(history_only_failures), 1)
        history_only_success = unify.get_queries(
            endpoints="gpt-4o@openai",
            start_time=self.start_time,
            failures=False,
        )
        self.assertEqual(len(history_only_success), 1)

        # Outside logged timeframe
        history_w_both = unify.get_queries(
            endpoints="gpt-4o@openai",
            start_time=datetime.now(timezone.utc) + timedelta(seconds=1),
            failures=True,
        )
        self.assertEqual(len(history_w_both), 0)
        history_only_failures = unify.get_queries(
            endpoints="gpt-4o@openai",
            start_time=datetime.now(timezone.utc) + timedelta(seconds=1),
            failures="only",
        )
        self.assertEqual(len(history_only_failures), 0)
        history_only_success = unify.get_queries(
            endpoints="gpt-4o@openai",
            start_time=datetime.now(timezone.utc) + timedelta(seconds=1),
            failures=False,
        )
        self.assertEqual(len(history_only_success), 0)

    def test_get_query_tags(self):
        unify.log_query(**self.data)
        tags = unify.get_query_tags()
        self.assertTrue(isinstance(tags, list))
        self.assertTrue(self.tag in tags)
