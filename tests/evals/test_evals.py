import unify
import random
import unittest


class TestEvals(unittest.TestCase):

    def _create_test_dataset(self):
        if "Test" in unify.utils.list_datasets():
            unify.utils.delete_dataset("Test")
        unify.utils.upload_dataset_from_file("Test", "prompts.jsonl")

    def test_run_eval(self) -> None:
        self._create_test_dataset()
        endpoints = random.sample(unify.endpoint.list_endpoints(), 10)
        unify.utils.evaluate("Test", endpoints)
