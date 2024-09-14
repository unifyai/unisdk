import os
import unittest

import unify
from unify.types import Prompt, Datum

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestDatasetConstruction(unittest.TestCase):

    def test_create_dataset_from_user_message(self) -> None:
        dataset = unify.Dataset("a")
        self.assertIsInstance(dataset[0], Datum)

    def test_create_dataset_from_list_of_user_messages(self) -> None:
        dataset = unify.Dataset(["a", "b", "c"])
        self.assertIsInstance(dataset[0], Datum)

    def test_create_dataset_from_prompt(self) -> None:
        dataset = unify.Dataset(Prompt(messages=[{"role": "user", "content": "a"}]))
        self.assertIsInstance(dataset[0], Datum)

    def test_create_dataset_from_list_of_prompts(self) -> None:
        dataset = unify.Dataset([Prompt(
            messages=[{"role": "user", "content": usr_msg}]
        ) for usr_msg in ["a", "b", "c"]])
        self.assertIsInstance(dataset[0], Datum)

    def test_create_dataset_from_prompt_dict(self) -> None:
        dataset = unify.Dataset(dict(messages=[{"role": "user", "content": "a"}]))
        self.assertIsInstance(dataset[0], Datum)

    def test_create_dataset_from_list_of_prompt_dicts(self) -> None:
        dataset = unify.Dataset([dict(
            messages=[{"role": "user", "content": usr_msg}]
        ) for usr_msg in ["a", "b", "c"]])
        self.assertIsInstance(dataset[0], Datum)

    def test_create_dataset_from_datum(self) -> None:
        dataset = unify.Dataset(Datum(
            prompt=Prompt(
                messages=[{"role": "user", "content": "a"}]
            )
        ))
        self.assertIsInstance(dataset[0], Datum)

    def test_create_dataset_from_list_of_data(self) -> None:
        dataset = unify.Dataset([Datum(
            prompt=Prompt(
                messages=[{"role": "user", "content": usr_msg}]
            )
        ) for usr_msg in ["a", "b", "c"]])
        self.assertIsInstance(dataset[0], Datum)

    def test_create_dataset_from_datum_dict(self) -> None:
        dataset = unify.Dataset(dict(
            prompt=Prompt(
                messages=[{"role": "user", "content": "a"}]
            )
        ))
        self.assertIsInstance(dataset[0], Datum)

    def test_create_dataset_from_list_of_datum_dicts(self) -> None:
        dataset = unify.Dataset([dict(
            prompt=Prompt(
                messages=[{"role": "user", "content": usr_msg}]
            )
        ) for usr_msg in ["a", "b", "c"]])
        self.assertIsInstance(dataset[0], Datum)

    def test_create_dataset_from_upstream(self) -> None:
        if "TestCreateDatasetFromStr" in unify.list_datasets():
            unify.delete_dataset("TestCreateDatasetFromStr")
        unify.upload_dataset_from_file(
            "TestCreateDatasetFromStr", os.path.join(dir_path, "prompts.jsonl")
        )
        assert "TestCreateDatasetFromStr" in unify.list_datasets()
        dataset = unify.Dataset.from_upstream("TestCreateDatasetFromStr")
        self.assertIsInstance(dataset[0], Datum)
        unify.delete_dataset("TestCreateDatasetFromStr")
        assert "TestCreateDatasetFromStr" not in unify.list_datasets()
