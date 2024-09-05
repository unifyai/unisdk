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
                    "messages":
                        [{
                            "role": "user",
                            "content": "This is the first user message"
                        }]
                },
                "ref_answer": "First reference answer",
            },
            {
                "prompt": {
                    "messages":
                        [{
                            "role": "user",
                            "content": "This is the second user message"
                        }]
                },
                "ref_answer": "Second reference answer",
            },
            {
                "prompt": {
                    "messages":
                        [{
                            "role": "user",
                            "content": "This is the third user message"
                        }]
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
