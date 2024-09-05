import os
import unittest

import unify
from unify.chat import Prompt
from unify.dataset import DatasetEntry

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestDatasets(unittest.TestCase):

    def test_create_dataset_from_list_of_prompts(self) -> None:
        dataset = unify.Dataset(["a", "b", "c"])
        self.assertIsInstance(dataset[0], DatasetEntry)

    def test_create_dataset_from_list_of_queries(self) -> None:
        dataset = unify.Dataset([Prompt(
            messages=[{"role": "user", "content": usr_msg}]
        ) for usr_msg in ["a", "b", "c"]])
        self.assertIsInstance(dataset[0], DatasetEntry)

    def test_create_dataset_from_list_of_query_dicts(self) -> None:
        dataset = unify.Dataset([dict(
            messages=[{"role": "user", "content": usr_msg}]
        ) for usr_msg in ["a", "b", "c"]])
        self.assertIsInstance(dataset[0], DatasetEntry)

    def test_create_dataset_from_list_of_entries(self) -> None:
        dataset = unify.Dataset([DatasetEntry(
            prompt=Prompt(
                messages=[{"role": "user", "content": usr_msg}]
            )
        ) for usr_msg in ["a", "b", "c"]])
        self.assertIsInstance(dataset[0], DatasetEntry)

    def test_create_dataset_from_list_of_entry_dicts(self) -> None:
        dataset = unify.Dataset([dict(
            prompt=Prompt(
                messages=[{"role": "user", "content": usr_msg}]
            )
        ) for usr_msg in ["a", "b", "c"]])
        self.assertIsInstance(dataset[0], DatasetEntry)

    def test_create_dataset_from_str(self) -> None:
        if "TestCreateDatasetFromStr" in unify.list_datasets():
            unify.delete_dataset("TestCreateDatasetFromStr")
        unify.upload_dataset_from_file(
            "TestCreateDatasetFromStr", os.path.join(dir_path, "prompts.jsonl")
        )
        assert "TestCreateDatasetFromStr" in unify.list_datasets()
        dataset = unify.Dataset("TestCreateDatasetFromStr")
        self.assertIsInstance(dataset[0], DatasetEntry)
        unify.delete_dataset("TestCreateDatasetFromStr")
        assert "TestCreateDatasetFromStr" not in unify.list_datasets()
