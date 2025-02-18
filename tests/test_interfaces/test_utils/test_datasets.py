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


if __name__ == "__main__":
    pass
