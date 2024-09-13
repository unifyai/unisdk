from datetime import datetime, timedelta
import unittest

from unify.utils import (
    get_query_tags,
    get_queries,
    log_query,
)


class TestLogQuery(unittest.TestCase):
    def setUp(self):
        self.start_time = datetime.now()
        query_time = self.start_time + timedelta(seconds=1)
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
                            "content": "Sir Isaac Newton was an English mathematician, physicist, and astronomer who lived from 1643 to 1727.\\n\\nHe is widely recognized as one of the most influential scientists in history, and his work laid the foundation for the Scientific Revolution of the 17th century.\\n\\nNewton's most famous achievement is his theory of universal gravitation, which he presented in his groundbreaking book \"Philosophi\\u00e6 Naturalis Principia Mathematica\" in 1687.\\n\\nAccording to Newton's theory, every",
                            "role": "assistant",
                        },
                    }
                ],
            },
            "timestamp": str(query_time),
            "tags": [self.tag],
        }

    def test_log_query(self):
        result = log_query(**self.data)
        self.assertIsInstance(result, dict)
        self.assertIn("info", result)
        self.assertEqual(result["info"], "Query logged successfully")
        history = get_queries(
            endpoints="local_model_test@external", start_time=str(self.start_time)
        )
        # check non-empty
        self.assertTrue(history)

    def test_get_tags(self):
        result = log_query(**self.data)
        tags = get_query_tags()
        self.assertTrue(isinstance(tags, list))
        self.assertTrue(self.tag in tags)

    def tearDown(self):
        pass
