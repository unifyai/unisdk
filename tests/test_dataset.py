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


# noinspection PyStatementEffect
class TestDatasetIndexing(unittest.TestCase):

    def test_iterate_over_dataset(self) -> None:
        msgs = ["a", "b", "c"]
        dataset = unify.Dataset(msgs)
        self.assertEqual(len(dataset), len(msgs))
        for datum, msg in zip(dataset, msgs):
            self.assertIsInstance(datum, Datum)
            self.assertEqual(datum.prompt.messages[0]["content"], msg)

    def test_index_dataset(self) -> None:
        dataset = unify.Dataset(["a", "b", "c"])
        self.assertIsInstance(dataset[0], Datum)
        self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")
        self.assertIsInstance(dataset[1], Datum)
        self.assertEqual(dataset[1].prompt.messages[0]["content"], "b")
        self.assertIsInstance(dataset[2], Datum)
        self.assertEqual(dataset[2].prompt.messages[0]["content"], "c")
        self.assertIsInstance(dataset[-1], Datum)
        self.assertEqual(dataset[-1].prompt.messages[0]["content"], "c")
        with self.assertRaises(IndexError):
            dataset[3]

    def test_slice_dataset(self) -> None:
        msgs = ["a", "b", "c", "d"]
        dataset = unify.Dataset(["a", "b", "c", "d"])
        msgs = msgs[1:-1]
        dataset = dataset[1:-1]
        for datum, msg in zip(dataset, msgs):
            self.assertIsInstance(datum, Datum)
            self.assertEqual(datum.prompt.messages[0]["content"], msg)

    def test_dataset_contains(self) -> None:
        dataset1 = unify.Dataset(["a", "b", "c"])
        dataset2 = unify.Dataset(["a", "b"])
        self.assertIn(dataset2, dataset1)
        self.assertIn("a", dataset1)
        self.assertIn(unify.Prompt("b"), dataset1)
        self.assertIn(["b", "c"], dataset1)
        self.assertNotIn("d", dataset1)
        dataset3 = unify.Dataset(["c", "d"])
        self.assertNotIn(dataset3, dataset1)


class TestDatasetCombining(unittest.TestCase):

    def test_add_datasets(self) -> None:
        msgs = ["a", "b", "c", "d"]
        dataset1 = unify.Dataset(msgs[0:2])
        dataset2 = unify.Dataset(msgs[2:])
        dataset = dataset1 + dataset2
        self.assertEqual(len(dataset), len(msgs))
        for datum, msg in zip(dataset, msgs):
            self.assertEqual(datum.prompt.messages[0]["content"], msg)

    def test_add_datasets_w_duplicates(self) -> None:
        msgs1 = ["a", "b"]
        msgs2 = ["b", "c"]
        dataset1 = unify.Dataset(msgs1)
        dataset2 = unify.Dataset(msgs2)
        dataset = dataset1 + dataset2
        self.assertEqual(len(dataset), 3)
        for datum, msg in zip(dataset, ("a", "b", "c")):
            self.assertEqual(datum.prompt.messages[0]["content"], msg)

    def test_dataset_inplace_addition(self) -> None:
        msgs = ["a", "b", "c", "d"]
        dataset = unify.Dataset(msgs[0:2])
        did = id(dataset)
        dataset2 = unify.Dataset(msgs[2:])
        dataset += dataset2
        self.assertEqual(did, id(dataset))
        self.assertEqual(len(dataset), len(msgs))
        for datum, msg in zip(dataset, msgs):
            self.assertEqual(datum.prompt.messages[0]["content"], msg)

    def test_dataset_single_item_addition(self) -> None:
        dataset = unify.Dataset("a") + "b"
        self.assertEqual(len(dataset), 2)
        self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")
        self.assertEqual(dataset[1].prompt.messages[0]["content"], "b")

    def test_dataset_reverse_addition(self) -> None:
        dataset = "a" + unify.Dataset("b")
        self.assertEqual(len(dataset), 2)
        self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")
        self.assertEqual(dataset[1].prompt.messages[0]["content"], "b")

    def test_dataset_from_prompt_addition(self) -> None:
        dataset = unify.Prompt("a") + unify.Prompt("b")
        self.assertEqual(len(dataset), 2)
        self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")
        self.assertEqual(dataset[1].prompt.messages[0]["content"], "b")

    def test_dataset_from_datum_addition(self) -> None:
        dataset = unify.Datum("a") + unify.Datum("b")
        self.assertEqual(len(dataset), 2)
        self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")
        self.assertEqual(dataset[1].prompt.messages[0]["content"], "b")

    def test_dataset_from_multi_item_addition(self) -> None:
        dataset = "a" + unify.Prompt("b") + unify.Datum("c")
        self.assertEqual(len(dataset), 3)
        self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")
        self.assertEqual(dataset[1].prompt.messages[0]["content"], "b")
        self.assertEqual(dataset[2].prompt.messages[0]["content"], "c")


class TestDatasetTrimming(unittest.TestCase):

    def test_sub_datasets(self) -> None:
        msgs = ["a", "b", "c", "d"]
        dataset1 = unify.Dataset(msgs)
        dataset2 = unify.Dataset(msgs[2:])
        dataset = dataset1 - dataset2
        self.assertEqual(len(dataset), 2)
        for datum, msg in zip(dataset, msgs[0:2]):
            self.assertEqual(datum.prompt.messages[0]["content"], msg)

    def test_sub_datasets_w_non_overlap(self) -> None:
        msgs1 = ["a", "b"]
        msgs2 = ["b", "c"]
        dataset1 = unify.Dataset(msgs1)
        dataset2 = unify.Dataset(msgs2)
        with self.assertRaises(AssertionError):
            dataset1 - dataset2

    def test_dataset_inplace_subtraction(self) -> None:
        msgs = ["a", "b", "c", "d"]
        dataset = unify.Dataset(msgs)
        did = id(dataset)
        dataset2 = unify.Dataset(msgs[2:])
        dataset -= dataset2
        self.assertEqual(did, id(dataset))
        self.assertEqual(len(dataset), 2)
        for datum, msg in zip(dataset, msgs[0:2]):
            self.assertEqual(datum.prompt.messages[0]["content"], msg)

    def test_dataset_single_item_subtraction(self) -> None:
        dataset = unify.Dataset(["a", "b"]) - "b"
        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")

    def test_dataset_reverse_subtraction(self) -> None:
        dataset = ["a", "b"] - unify.Dataset("b")
        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")

    def test_dataset_from_prompt_subtraction(self) -> None:
        dataset = unify.Prompt("b") + unify.Prompt("a") - unify.Prompt("b")
        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")

    def test_dataset_from_datum_subtraction(self) -> None:
        dataset = unify.Datum("b") + unify.Datum("a") - unify.Datum("b")
        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")


class UploadTesting:

    def __enter__(self):
        if "test_dataset" in unify.list_datasets():
            unify.delete_dataset("test_dataset")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if "test_dataset" in unify.list_datasets():
            unify.delete_dataset("test_dataset")


class TestDatasetUploading(unittest.TestCase):

    def test_dataset_first_upload(self) -> None:
        with UploadTesting():
            dataset = unify.Dataset(["a", "b", "c"], name="test_dataset")
            self.assertNotIn(dataset.name, unify.list_datasets())
            dataset.upload()
            self.assertIn(dataset.name, unify.list_datasets())

    def test_dataset_upload_w_overwrite(self) -> None:
        with UploadTesting():
            dataset = unify.Dataset(["a", "b", "c"], name="test_dataset")
            self.assertNotIn(dataset.name, unify.list_datasets())
            dataset.upload()
            self.assertIn(dataset.name, unify.list_datasets())
            self.assertEqual(len(unify.Dataset.from_upstream("test_dataset")), 3)
            dataset -= "c"
            dataset.upload(overwrite=True)
            self.assertEqual(len(unify.Dataset.from_upstream("test_dataset")), 2)

    def test_dataset_upload_wo_overwrite(self):
        with UploadTesting():
            dataset = unify.Dataset(["a", "b", "c"], name="test_dataset")
            self.assertNotIn(dataset.name, unify.list_datasets())
            dataset.upload()
            self.assertIn(dataset.name, unify.list_datasets())
            self.assertEqual(len(unify.Dataset.from_upstream("test_dataset")), 3)
            dataset += "d"
            dataset.upload()
            self.assertEqual(len(unify.Dataset.from_upstream("test_dataset")), 4)


class DownloadTesting:

    def __enter__(self):
        if "test_dataset" in unify.list_datasets():
            unify.delete_dataset("test_dataset")
        dataset = unify.Dataset(["a", "b", "c"], name="test_dataset")
        dataset.upload()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if "test_dataset" in unify.list_datasets():
            unify.delete_dataset("test_dataset")


# noinspection PyStatementEffect
class TestDatasetDownloading(unittest.TestCase):

    def test_dataset_download(self) -> None:
        with DownloadTesting():
            self.assertIn("test_dataset", unify.list_datasets())
            dataset = unify.Dataset.from_upstream("test_dataset")
            # noinspection DuplicatedCode
            self.assertEqual(len(dataset), 3)
            self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")
            self.assertEqual(dataset[1].prompt.messages[0]["content"], "b")
            self.assertEqual(dataset[2].prompt.messages[0]["content"], "c")

    def test_dataset_download_w_overwrite(self) -> None:
        with DownloadTesting():
            self.assertIn("test_dataset", unify.list_datasets())
            dataset = unify.Dataset(["a", "b", "c", "d"], name="test_dataset")
            self.assertEqual(len(dataset), 4)
            self.assertEqual(dataset[3].prompt.messages[0]["content"], "d")
            dataset.download(overwrite=True)
            self.assertEqual(len(dataset), 3)
            with self.assertRaises(IndexError):
                dataset[3]


class TestDatasetSync(unittest.TestCase):

    def test_sync_uploads(self) -> None:
        with DownloadTesting():
            self.assertIn("test_dataset", unify.list_datasets())
            dataset = unify.Dataset(["a", "b", "c", "d"], name="test_dataset")
            dataset.sync()
            dataset.download()
            self.assertEqual(len(dataset), 4)
            self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")
            self.assertEqual(dataset[1].prompt.messages[0]["content"], "b")
            self.assertEqual(dataset[2].prompt.messages[0]["content"], "c")
            self.assertEqual(dataset[3].prompt.messages[0]["content"], "d")

    def test_sync_downloads(self) -> None:
        with DownloadTesting():
            self.assertIn("test_dataset", unify.list_datasets())
            dataset = unify.Dataset(["a", "b"], name="test_dataset")
            dataset.sync()
            dataset.download()
            self.assertEqual(len(dataset), 3)
            self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")
            self.assertEqual(dataset[1].prompt.messages[0]["content"], "b")
            self.assertEqual(dataset[2].prompt.messages[0]["content"], "c")

    def test_sync_achieves_superset(self) -> None:
        with DownloadTesting():
            self.assertIn("test_dataset", unify.list_datasets())
            dataset = unify.Dataset(["a", "b", "d"], name="test_dataset")
            dataset.sync()
            self.assertEqual(len(dataset), 4)
            self.assertEqual(dataset[0].prompt.messages[0]["content"], "a")
            self.assertEqual(dataset[1].prompt.messages[0]["content"], "b")
            self.assertEqual(dataset[2].prompt.messages[0]["content"], "c")
            self.assertEqual(dataset[3].prompt.messages[0]["content"], "d")

    def test_auto_sync(self) -> None:
        with DownloadTesting():
            dataset = unify.Dataset(
                ["a", "b", "d"],
                name="test_dataset",
                auto_sync=True
            )
            self.assertEqual(len(dataset), 4)
            for i, char in enumerate(("a", "b", "c", "d")):
                self.assertEqual(dataset[i].prompt.messages[0]["content"], char)
