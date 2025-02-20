import unify

from ..helpers import _handle_project


@_handle_project
def test_list_datasets():
    assert len(unify.list_datasets()) == 0
    unify.log(x=0, context="Datasets/Prod/TestSet")
    unify.log(x=1, context="Datasets/Prod/TestSet")
    unify.log(x=0, context="Datasets/Eval/ValidationSet")
    unify.log(x=1, context="Datasets/Eval/ValidationSet")
    datasets = unify.list_datasets()
    assert len(datasets) == 2
    assert "Prod/TestSet" in datasets
    assert "Eval/ValidationSet" in datasets
    datasets = unify.list_datasets(prefix="Prod")
    assert len(datasets) == 1
    assert "Prod/TestSet" in datasets
    assert "Eval/ValidationSet" not in datasets
    datasets = unify.list_datasets(prefix="Eval")
    assert len(datasets) == 1
    assert "Eval/ValidationSet" in datasets
    assert "Prod/TestSet" not in datasets


@_handle_project
def test_upload_dataset():
    dataset = [
        {
            "name": "Dan",
            "age": 31,
            "gender": "male",
        },
        {
            "name": "Jane",
            "age": 25,
            "gender": "female",
        },
        {
            "name": "John",
            "age": 35,
            "gender": "male",
        },
    ]
    data = unify.upload_dataset("staff", dataset)
    assert len(data) == 3


@_handle_project
def test_add_dataset_entries():
    dataset = [
        {
            "name": "Dan",
            "age": 31,
            "gender": "male",
        },
        {
            "name": "Jane",
            "age": 25,
            "gender": "female",
        },
        {
            "name": "John",
            "age": 35,
            "gender": "male",
        },
    ]
    ids = unify.upload_dataset("staff", dataset)
    assert len(ids) == 3
    dataset = unify.download_dataset("staff")
    assert len(dataset) == 3
    assert dataset[0].entries["name"] == "Dan"
    assert dataset[1].entries["name"] == "Jane"
    assert dataset[2].entries["name"] == "John"
    new_entries = [
        {
            "name": "Chloe",
            "age": 28,
            "gender": "female",
        },
        {
            "name": "Tom",
            "age": 32,
            "gender": "male",
        },
    ]
    ids = unify.add_dataset_entries("staff", new_entries)
    assert len(ids) == 2
    dataset = unify.download_dataset("staff")
    assert len(dataset) == 5
    assert dataset[0].entries["name"] == "Dan"
    assert dataset[1].entries["name"] == "Jane"
    assert dataset[2].entries["name"] == "John"
    assert dataset[3].entries["name"] == "Chloe"
    assert dataset[4].entries["name"] == "Tom"


@_handle_project
def test_download_dataset():
    dataset = [
        {
            "name": "Dan",
            "age": 31,
            "gender": "male",
        },
        {
            "name": "Jane",
            "age": 25,
            "gender": "female",
        },
        {
            "name": "John",
            "age": 35,
            "gender": "male",
        },
    ]
    unify.upload_dataset("staff", dataset)
    data = unify.download_dataset("staff")
    assert len(data) == 3


@_handle_project
def test_delete_dataset():
    dataset = [
        {
            "name": "Dan",
            "age": 31,
            "gender": "male",
        },
        {
            "name": "Jane",
            "age": 25,
            "gender": "female",
        },
        {
            "name": "John",
            "age": 35,
            "gender": "male",
        },
    ]
    unify.upload_dataset("staff", dataset)
    unify.delete_dataset("staff")
    assert "staff" not in unify.list_datasets()


if __name__ == "__main__":
    pass
