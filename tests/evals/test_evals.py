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
        # ToDo: replace with below once HTTP API is fixed
        # endpoint_availability = unify.endpoint_availability.list_endpoints()
        endpoints = []
        for model in unify.utils.list_models():
            endpoints += unify.utils.list_endpoints(model)
        endpoints = random.sample(endpoints, 10)
        unify.utils.evaluate("Test", endpoints)
