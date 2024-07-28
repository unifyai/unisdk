import unify
import unittest


class TestDatasets(unittest.TestCase):

    def test_upload_and_delete_dataset_from_file(self) -> None:
        if "Test" in unify.utils.list_datasets():
            unify.utils.delete_dataset("Test")
        unify.utils.upload_dataset_from_file("Test", "prompts.jsonl")
        assert "Test" in unify.utils.list_datasets()
        unify.utils.delete_dataset("Test")
        assert unify.utils.list_datasets() == []

    def test_upload_and_delete_dataset_from_dict(self) -> None:
        prompts = [{"prompt": "This is the first prompt", "ref_answer": "First reference answer"},
                   {"prompt": "This is the second prompt", "ref_answer": "Second reference answer"},
                   {"prompt": "This is the third prompt", "ref_answer": "Third reference answer"}]
        if "Test" in unify.utils.list_datasets():
            unify.utils.delete_dataset("Test")
        unify.utils.upload_dataset_from_dictionary("Test", prompts)
        assert "Test" in unify.utils.list_datasets()
        unify.utils.delete_dataset("Test")
        assert unify.utils.list_datasets() == []
