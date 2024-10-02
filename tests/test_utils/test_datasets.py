import os
import unify
import unittest

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestDatasets(unittest.TestCase):

    def test_upload_and_delete_dataset_from_file(self) -> None:
        if "TestUploadAndDelete" in unify.list_datasets():
            unify.delete_dataset("TestUploadAndDelete")
        unify.upload_dataset_from_file(
            "TestUploadAndDelete", os.path.join(dir_path, "prompts.jsonl")
        )
        assert "TestUploadAndDelete" in unify.list_datasets()
        unify.delete_dataset("TestUploadAndDelete")
        assert "TestUploadAndDelete" not in unify.list_datasets()

    def test_upload_and_delete_dataset_from_dict(self) -> None:
        entries = [
            {
                "prompt": {
                    "messages": [
                        {"role": "user", "content": "This is the first user message"}
                    ]
                },
                "ref_answer": "First reference answer",
            },
            {
                "prompt": {
                    "messages": [
                        {"role": "user", "content": "This is the second user message"}
                    ]
                },
                "ref_answer": "Second reference answer",
            },
            {
                "prompt": {
                    "messages": [
                        {"role": "user", "content": "This is the third user message"}
                    ]
                },
                "ref_answer": "Third reference answer",
            },
        ]
        if "TestFromDict" in unify.list_datasets():
            unify.delete_dataset("TestFromDict")
        unify.upload_dataset_from_dictionary("TestFromDict", entries)
        assert "TestFromDict" in unify.list_datasets()
        unify.delete_dataset("TestFromDict")
        assert "TestFromDict" not in unify.list_datasets()

    def test_atomic_functions(self):
        entries = [
            {
                "prompt": {
                    "messages": [
                        {"role": "user", "content": "This is the first user message"}
                    ]
                },
                "ref_answer": "First reference answer",
            },
            {
                "prompt": {
                    "messages": [
                        {"role": "user", "content": "This is the second user message"}
                    ]
                },
                "ref_answer": "Second reference answer",
            },
            {
                "prompt": {
                    "messages": [
                        {"role": "user", "content": "This is the third user message"}
                    ]
                },
                "ref_answer": "Third reference answer",
            },
        ]

        dataset_name = "TestAtomic"
        if dataset_name in unify.list_datasets():
            unify.delete_dataset(dataset_name)
        unify.upload_dataset_from_dictionary(dataset_name, entries)

        new_prompt_data = {
            "prompt": {
                "messages": [
                    {"role": "user", "content": "What is the powerhouse of the cell?"}
                ]
            }
        }
        unify.datasets.add_data(dataset_name, new_prompt_data)
        data = unify.datasets.download_dataset(dataset_name)
        self.assertTrue(len(data)==4)

        _id = data[0]["id"]
        unify.datasets.delete_data(dataset_name, _id, )
        data = unify.datasets.download_dataset(dataset_name)
        self.assertTrue(len(data)==3)

        unify.datasets.rename_dataset("TestAtomic", "RenamedTestAtomic")
        self.assertIn("RenamedTestAtomic", unify.datasets.list_datasets())
        unify.delete_dataset("RenamedTestAtomic")
