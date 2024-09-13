import unittest
import time

import unify
from unify.utils import (
    create_evaluator,
    trigger_evaluation,
    get_evaluations,
    delete_evaluator,
    delete_evaluations,
)
from unify.utils.datasets import delete_dataset


class TestTriggerEvaluation(unittest.TestCase):
    def setUp(self):
        entries = [
            {
                "prompt": {
                    "messages": [
                        {"role": "user", "content": "What is the capital of Spain?"}
                    ]
                },
                "ref_answer": "Madrid",
            },
            {
                "prompt": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "What is the square root of 1009 to 1 decimal place",
                        }
                    ]
                },
                "ref_answer": "31.8",
            },
        ]
        try:
            unify.upload_dataset_from_dictionary("TestTrigger", entries)
        except:
            pass

    def test_trigger_evaluation(self):
        response = trigger_evaluation(
            evaluator="default_evaluator",
            dataset="TestTrigger",
            endpoint="llama-3-8b-chat@aws-bedrock",
        )
        self.assertIn("info", response)
        self.assertEqual(
            response["info"],
            "Dataset evaluation started! You will receive an email soon!",
        )

        time.sleep(10)
        output = get_evaluations(dataset="TestTrigger", evaluator="default_evaluator")
        self.assertIn("default_evaluator", output)
        self.assertIn("llama-3-8b-chat@aws-bedrock", output["default_evaluator"])
        self.assertIn(
            "score", output["default_evaluator"]["llama-3-8b-chat@aws-bedrock"]
        )
        self.assertIn(
            "progress", output["default_evaluator"]["llama-3-8b-chat@aws-bedrock"]
        )

        delete_evaluations(dataset="TestTrigger")
        output = get_evaluations(dataset="TestTrigger", evaluator="default_evaluator")
        self.assertEqual(len(output), 0)

    def tearDown(self):
        try:
            delete_evaluations(dataset="TestTrigger")
            delete_dataset("TestTrigger")
        except:
            pass
