import unify
import unittest


class TestDatasets(unittest.TestCase):
    def test_upload_and_delete_dataset_from_file(self) -> None:
        if "TestUploadAndDelete" in unify.list_datasets():
            unify.delete_dataset("TestUploadAndDelete")
        unify.upload_dataset_from_file(
            "TestUploadAndDelete", "./tests/datasets/prompts.jsonl"
        )
        assert "TestUploadAndDelete" in unify.list_datasets()
        unify.delete_dataset("TestUploadAndDelete")
        assert "TestUploadAndDelete" not in unify.list_datasets()

    def test_upload_and_delete_dataset_from_dict(self) -> None:
        prompts = [
            {
                "prompt": "This is the first prompt",
                "ref_answer": "First reference answer",
            },
            {
                "prompt": "This is the second prompt",
                "ref_answer": "Second reference answer",
            },
            {
                "prompt": "This is the third prompt",
                "ref_answer": "Third reference answer",
            },
        ]
        if "TestFromDict" in unify.list_datasets():
            unify.delete_dataset("TestFromDict")
        unify.upload_dataset_from_dictionary("TestFromDict", prompts)
        assert "TestFromDict" in unify.list_datasets()
        unify.delete_dataset("TestFromDict")
        assert "TestFromDict" not in unify.list_datasets()
