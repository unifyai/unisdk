import os
import random
import string
import unittest

import unify
from unify.types import Prompt

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestDatasetConstruction(unittest.TestCase):

    def test_create_dataset_from_str(self) -> None:
        dataset = unify.Dataset("a")
        self.assertIsInstance(dataset[0], str)

    def test_create_dataset_from_list_of_str(self) -> None:
        dataset = unify.Dataset(["a", "b", "c"])
        self.assertIsInstance(dataset[0], str)

    def test_create_dataset_from_prompt(self) -> None:
        dataset = unify.Dataset(Prompt(messages=[{"role": "user", "content": "a"}]))
        self.assertIsInstance(dataset[0], Prompt)

    def test_create_dataset_from_list_of_prompts(self) -> None:
        dataset = unify.Dataset(
            [
                Prompt(messages=[{"role": "user", "content": usr_msg}])
                for usr_msg in ["a", "b", "c"]
            ],
        )
        self.assertIsInstance(dataset[0], Prompt)

    def test_create_dataset_from_dict(self) -> None:
        dataset = unify.Dataset(dict(messages=[{"role": "user", "content": "a"}]))
        self.assertIsInstance(dataset[0], dict)

    def test_create_dataset_from_list_of_dicts(self) -> None:
        dataset = unify.Dataset(
            [
                dict(messages=[{"role": "user", "content": usr_msg}])
                for usr_msg in ["a", "b", "c"]
            ],
        )
        self.assertIsInstance(dataset[0], dict)

    def test_create_dataset_from_dict_w_prompt(self) -> None:
        dataset = unify.Dataset(
            dict(prompt=Prompt(messages=[{"role": "user", "content": "a"}])),
        )
        self.assertIsInstance(dataset[0], dict)

    def test_create_dataset_from_list_of_prompt_dicts(self) -> None:
        dataset = unify.Dataset(
            [
                dict(prompt=Prompt(messages=[{"role": "user", "content": usr_msg}]))
                for usr_msg in ["a", "b", "c"]
            ],
        )
        self.assertIsInstance(dataset[0], dict)

    def test_create_dataset_from_upstream(self) -> None:
        if "TestCreateDatasetFromStr" in unify.list_datasets():
            unify.delete_dataset("TestCreateDatasetFromStr")

        dataset = unify.Dataset(["a", "b", "c"], name="TestCreateDatasetFromStr")
        self.assertNotIn(dataset.name, unify.list_datasets())
        dataset.upload()
        assert "TestCreateDatasetFromStr" in unify.list_datasets()
        dataset = unify.Dataset.from_upstream("TestCreateDatasetFromStr")
        self.assertIsInstance(dataset._raw_data[0], dict)
        unify.delete_dataset("TestCreateDatasetFromStr")
        assert "TestCreateDatasetFromStr" not in unify.list_datasets()


# noinspection PyStatementEffect
class TestDatasetManipulation(unittest.TestCase):

    def test_iterate_over_dataset(self) -> None:
        msgs = ["a", "b", "c"]
        dataset = unify.Dataset(msgs)
        self.assertEqual(len(dataset), len(msgs))
        for item, msg in zip(dataset, msgs):
            self.assertIsInstance(item, str)
            self.assertEqual(item, msg)

    def test_index_dataset(self) -> None:
        dataset = unify.Dataset(["a", "b", "c"])
        self.assertIsInstance(dataset[0], str)
        self.assertEqual(dataset[0], "a")
        self.assertIsInstance(dataset[1], str)
        self.assertEqual(dataset[1], "b")
        self.assertIsInstance(dataset[2], str)
        self.assertEqual(dataset[2], "c")
        self.assertIsInstance(dataset[-1], str)
        self.assertEqual(dataset[-1], "c")
        with self.assertRaises(IndexError):
            dataset[3]

    def test_slice_dataset(self) -> None:
        msgs = ["a", "b", "c", "d"]
        dataset = unify.Dataset(["a", "b", "c", "d"])
        msgs = msgs[1:-1]
        dataset = dataset[1:-1]
        for item, msg in zip(dataset, msgs):
            self.assertIsInstance(item, str)
            self.assertEqual(item, msg)

    def test_dataset_contains(self) -> None:
        dataset1 = unify.Dataset(["a", "b", "c"])
        dataset2 = unify.Dataset(["a", "b"])
        self.assertIn(dataset2, dataset1)
        self.assertIn("a", dataset1)
        self.assertIn("b", dataset1)
        self.assertIn(["b", "c"], dataset1)
        self.assertNotIn("d", dataset1)
        dataset3 = unify.Dataset(["c", "d"])
        self.assertNotIn(dataset3, dataset1)

    def test_dataset_one_liners(self) -> None:
        dataset = ("a" + unify.Prompt("b")).add("c").set_name("my_dataset")
        self.assertEqual(dataset.name, "my_dataset")
        self.assertIn("a", dataset)
        self.assertIn(unify.Prompt("b"), dataset)
        self.assertIn("c", dataset)


class TestDatasetCombining(unittest.TestCase):

    def test_add_datasets(self) -> None:
        msgs = ["a", "b", "c", "d"]
        dataset1 = unify.Dataset(msgs[0:2])
        dataset2 = unify.Dataset(msgs[2:])
        dataset = dataset1 + dataset2
        self.assertEqual(len(dataset), len(msgs))
        for item, msg in zip(dataset, msgs):
            self.assertEqual(item, msg)

    def test_sum_datasets(self) -> None:
        msgs = ["a", "b", "c", "d"]
        dataset1 = unify.Dataset(msgs[0:2])
        dataset2 = unify.Dataset(msgs[2:])
        dataset = sum([dataset1, dataset2])
        self.assertEqual(len(dataset), len(msgs))
        for item, msg in zip(dataset, msgs):
            self.assertEqual(item, msg)

    def test_sum_variety(self) -> None:
        msgs = [unify.Prompt("a"), "b", unify.Prompt("c"), "d"]
        dataset = sum(msgs)
        self.assertEqual(len(dataset), len(msgs))
        for item, msg in zip(dataset, msgs):
            self.assertEqual(unify.cast(item, str), unify.cast(msg, str))

    def test_add_datasets_w_duplicates(self) -> None:
        msgs1 = ["a", "b"]
        msgs2 = ["b", "c"]
        dataset1 = unify.Dataset(msgs1)
        dataset2 = unify.Dataset(msgs2)
        dataset = dataset1 + dataset2
        self.assertEqual(len(dataset), 3)
        for item, msg in zip(dataset, ("a", "b", "c")):
            self.assertEqual(item, msg)

    def test_dataset_inplace_addition(self) -> None:
        msgs = ["a", "b", "c", "d"]
        dataset = unify.Dataset(msgs[0:2])
        did = id(dataset)
        dataset2 = unify.Dataset(msgs[2:])
        dataset += dataset2
        self.assertEqual(did, id(dataset))
        self.assertEqual(len(dataset), len(msgs))
        for item, msg in zip(dataset, msgs):
            self.assertEqual(item, msg)

    def test_dataset_single_item_addition(self) -> None:
        dataset = unify.Dataset("a") + "b"
        self.assertEqual(len(dataset), 2)
        self.assertEqual(dataset[0], "a")
        self.assertEqual(dataset[1], "b")

    def test_dataset_reverse_addition(self) -> None:
        dataset = "a" + unify.Dataset("b")
        self.assertEqual(len(dataset), 2)
        self.assertEqual(dataset[0], "a")
        self.assertEqual(dataset[1], "b")

    def test_dataset_from_prompt_addition(self) -> None:
        dataset = unify.Prompt("a") + unify.Prompt("b")
        self.assertEqual(len(dataset), 2)
        self.assertEqual(dataset[0], unify.Prompt("a"))
        self.assertEqual(dataset[1], unify.Prompt("b"))

    def test_dataset_from_multi_item_addition(self) -> None:
        dataset = "a" + unify.Prompt("b") + "c"
        self.assertEqual(len(dataset), 3)
        self.assertEqual(dataset[0], "a")
        self.assertEqual(dataset[1], unify.Prompt("b"))
        self.assertEqual(dataset[2], "c")


class TestDatasetTrimming(unittest.TestCase):

    def test_sub_datasets(self) -> None:
        msgs = ["a", "b", "c", "d"]
        dataset1 = unify.Dataset(msgs)
        dataset2 = unify.Dataset(msgs[2:])
        dataset = dataset1 - dataset2
        self.assertEqual(len(dataset), 2)
        for item, msg in zip(dataset, msgs[0:2]):
            self.assertEqual(item, msg)

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
        for item, msg in zip(dataset, msgs[0:2]):
            self.assertEqual(item, msg)

    def test_dataset_single_item_subtraction(self) -> None:
        dataset = unify.Dataset(["a", "b"]) - "b"
        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0], "a")

    def test_dataset_reverse_subtraction(self) -> None:
        dataset = ["a", "b"] - unify.Dataset("b")
        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0], "a")

    def test_dataset_from_prompt_subtraction(self) -> None:
        dataset = unify.Prompt("b") + unify.Prompt("a") - unify.Prompt("b")
        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0], unify.Prompt("a"))


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
        unify.Dataset(["a", "b", "c"], name="test_dataset").upload()

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
            self.assertEqual(dataset[0], "a")
            self.assertEqual(dataset[1], "b")
            self.assertEqual(dataset[2], "c")

    def test_dataset_download_w_overwrite(self) -> None:
        with DownloadTesting():
            self.assertIn("test_dataset", unify.list_datasets())
            dataset = unify.Dataset(["a", "b", "c", "d"], name="test_dataset")
            self.assertEqual(len(dataset), 4)
            self.assertEqual(dataset[3], "d")
            dataset.download(overwrite=True)
            self.assertEqual(len(dataset), 3)
            with self.assertRaises(IndexError):
                dataset[3]

    def test_dataset_download_dict(self) -> None:
        if "test_dataset" in unify.list_datasets():
            unify.delete_dataset("test_dataset")
        msgs = ("a", "b", "c")
        extra = ("A", "B", "C")
        extra_name = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
        data = [{"message": msg, extra_name: ans} for msg, ans in zip(msgs, extra)]
        dataset = unify.Dataset(data, name="test_dataset")
        self.assertIn("message", dataset[0])
        self.assertIn(extra_name, dataset[0])
        dataset.upload()
        dataset = unify.Dataset.from_upstream("test_dataset")
        for i, (msg, ans) in enumerate(zip(msgs, extra)):
            self.assertIn("message", dataset[i])
            self.assertEqual(dataset[i]["message"], msg)
            self.assertIn(extra_name, dataset[i])
            self.assertEqual(dataset[i][extra_name], ans)
        unify.delete_dataset("test_dataset")

    def test_dataset_downloading_prompt_ids(self) -> None:
        with DownloadTesting():
            dataset = unify.Dataset.from_upstream("test_dataset")
            id_collection = list()
            for item in dataset._raw_data:
                self.assertIn("id", item)
                self.assertIn("entry", item)
                self.assertIsInstance(item["id"], str)


class TestDatasetSync(unittest.TestCase):

    def test_sync_uploads(self) -> None:
        with DownloadTesting():
            self.assertIn("test_dataset", unify.list_datasets())
            dataset = unify.Dataset(["a", "b", "c", "d"], name="test_dataset")
            dataset.sync()
            dataset.download()
            self.assertEqual(len(dataset), 4)
            self.assertEqual(dataset[0], "a")
            self.assertEqual(dataset[1], "b")
            self.assertEqual(dataset[2], "c")
            self.assertEqual(dataset[3], "d")

    def test_sync_downloads(self) -> None:
        with DownloadTesting():
            self.assertIn("test_dataset", unify.list_datasets())
            dataset = unify.Dataset(["a", "b"], name="test_dataset")
            dataset.sync()
            dataset.download()
            self.assertEqual(len(dataset), 3)
            self.assertEqual(dataset[0], "a")
            self.assertEqual(dataset[1], "b")
            self.assertEqual(dataset[2], "c")

    def test_sync_achieves_superset(self) -> None:
        with DownloadTesting():
            self.assertIn("test_dataset", unify.list_datasets())
            dataset = unify.Dataset(["a", "b", "d"], name="test_dataset")
            dataset.sync()
            self.assertEqual(len(dataset), 4)
            self.assertEqual(dataset[0], "a")
            self.assertEqual(dataset[1], "b")
            self.assertEqual(dataset[2], "c")
            self.assertEqual(dataset[3], "d")
