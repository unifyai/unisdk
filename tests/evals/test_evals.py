import unify
import random
import unittest


def _create_test_dataset():
    if "Test" in unify.list_datasets():
        unify.delete_dataset("Test")
    unify.upload_dataset_from_file("Test", "./tests/evals/prompts.jsonl")


class TestEvals(unittest.TestCase):
    def test_run_eval(self) -> None:
        _create_test_dataset()
        endpoints = random.sample(unify.list_endpoints(), 2)
        unify.evaluate("Test", endpoints)
