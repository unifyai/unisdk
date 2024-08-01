import unify
import random
import unittest


def _create_test_dataset():
    if "Test" in unify.utils.list_datasets():
        unify.utils.delete_dataset("Test")
    unify.utils.upload_dataset_from_file("Test", "prompts.jsonl")


class TestEvals(unittest.TestCase):

    def test_run_eval(self) -> None:
        _create_test_dataset()
        endpoints = random.sample(unify.utils.list_endpoints(), 2)
        unify.utils.evaluate("Test", endpoints)
