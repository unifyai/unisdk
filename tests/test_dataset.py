import os
import unittest

import unify
from unify.queries import Query
from unify.dataset import DatasetEntry

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestDatasets(unittest.TestCase):

    def test_create_dataset_from_list_of_prompts(self) -> None:
        dataset = unify.Dataset(["a", "b", "c"])
        self.assertIsInstance(dataset[0], DatasetEntry)

    def test_create_dataset_from_list_of_queries(self) -> None:
        dataset = unify.Dataset([Query(
            messages=[{"role": "user", "content": prompt}]
        ) for prompt in ["a", "b", "c"]])
        self.assertIsInstance(dataset[0], DatasetEntry)

    def test_create_dataset_from_list_of_entries(self) -> None:
        dataset = unify.Dataset([DatasetEntry(
            query=Query(
                messages=[{"role": "user", "content": prompt}]
            )
        ) for prompt in ["a", "b", "c"]])
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
