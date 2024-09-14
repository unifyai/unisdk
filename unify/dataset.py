from __future__ import annotations
from typing import List, Dict, Union, Optional

import unify
from unify.types import _Formatted
from unify.types import Prompt, Datum
from .utils.helpers import _validate_api_key, _dict_aligns_with_pydantic


class Dataset(_Formatted):
    def __init__(
        self,
        data: Union[str, Dict, Prompt, Datum,
                    List[Union[str, Dict, Prompt, Datum]]],
        *,
        name: str = None,
        auto_sync: Union[bool, str] = False,
        api_key: Optional[str] = None,
    ):
        """
        Initialize a local dataset of LLM queries.

        Args:
            data: The data for populating the dataset. This can either can a list of
            user messages, a list of full queries, or a list of dicts of queries
            alongside any extra fields. Individual items in any of the formats listed
            above will also be converted to lists and processed automatically.

            name: The name of the dataset.

            auto_sync: Whether to automatically keep this dataset fully synchronized
            with the upstream variant at all times. If `True` or "both" then the sync
            will be bi-directional, if "upload_only" then all local changes will be
            uploaded to the upstream account without any downloads, if "download_only"
            then all upstream changes will be downloaded locally without any uploads.
            If `False` or "neither" then no synchronization will be done automatically.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.

        Raises:
            UnifyError: If the API key is missing.
        """
        self._name = name
        if isinstance(data, tuple):
            data = list(data)
        elif not isinstance(data, list):
            data = [data]
        if isinstance(data[0], str):
            self._data =\
                [Datum(prompt=Prompt(
                    messages=[{"role": "user", "content": usr_msg}]
                ))
                    for usr_msg in data]
        elif isinstance(data[0], Prompt):
            self._data = [Datum(prompt=prompt) for prompt in data]
        elif isinstance(data[0], dict) and _dict_aligns_with_pydantic(data[0], Prompt):
            self._data = [Datum(prompt=Prompt(**dct)) for dct in data]
        elif isinstance(data[0], Datum):
            self._data = data
        elif isinstance(data[0], dict) and \
                _dict_aligns_with_pydantic(data[0], Datum):
            self._data = self._data = [Datum(**dct) for dct in data]
        else:
            raise Exception("input {} with entries of type {} does not align with "
                            "expected input types.".format(data, type(data[0])))
        self._api_key = _validate_api_key(api_key)
        self._auto_sync_flag = auto_sync
        self._auto_sync()

    @property
    def name(self) -> str:
        return self._name

    @property
    def auto_sync(self) -> Union[bool, str]:
        return self._auto_sync_flag

    def set_name(self, name: str) -> None:
        self._name = name

    def set_auto_sync(self, auto_sync: Union[bool, str]) -> None:
        self._auto_sync_flag = auto_sync

    @staticmethod
    def from_upstream(
        name: str,
        auto_sync: bool = False,
        api_key: Optional[str] = None,
    ):
        """
        Initialize a local dataset of LLM queries, from the upstream dataset.

        Args:
            name: The name of the dataset.

            auto_sync: Whether to automatically keep this dataset fully synchronized
            with the upstream variant at all times.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.

        Raises:
            UnifyError: If the API key is missing.
        """
        data = unify.download_dataset(name, api_key=api_key)
        return Dataset(data, name=name, auto_sync=auto_sync, api_key=api_key)

    def _assert_name_exists(self):
        assert self._name is not None, (
            "Dataset name must be specified in order to upload, download, sync or "
            "compare to a corresponding dataset in your upstream account. "
            "You can simply use .set_name() and set it to the same name as your "
            "upstream dataset, or create a new name if it doesn't yet exist upstream."
        )

    def upload(self, overwrite=False):
        """
        Uploads all unique local data in the dataset to the user account upstream.
        This function will not download any uniques from upstream.
        Use `sync` to synchronize and superset the datasets in both directions.
        Set `overwrite=True` to disregard any pre-existing upstream data.

        Args:
            overwrite: Whether to overwrite the upstream dataset if it already exists
        """
        self._assert_name_exists()
        dataset_exists_upstream = self._name in unify.list_datasets(self._api_key)
        if overwrite:
            if dataset_exists_upstream:
                unify.delete_dataset(self._name, self._api_key)
            unify.upload_dataset_from_dictionary(self._name, self._data)
            return
        if dataset_exists_upstream:
            upstream_dataset = unify.download_dataset(self._name, api_key=self._api_key)
            unique_local_data = list(set(self._data) - set(upstream_dataset))
            unify.add_prompt(self._name, unique_local_data)
        else:
            unique_local_data = [entry.dict() for entry in self._data]
            unify.upload_dataset_from_dictionary(self._name, unique_local_data)
        if self._auto_sync_flag in (True, "both", "download_only"):
            self.download()

    def download(self, overwrite=False):
        """
        Downloads all unique upstream data from the user account to the local dataset.
        This function will not upload any unique values stored locally.
        Use `sync` to synchronize and superset the datasets in both directions.
        Set `overwrite=True` to disregard any pre-existing data stored in this class.

        Args:
            overwrite: Whether to overwrite the local data, if any already exists
        """
        self._assert_name_exists()
        if overwrite:
            self._data = unify.download_dataset(self._name, api_key=self._api_key)
            return
        upstream_dataset = unify.download_dataset(self._name, api_key=self._api_key)
        unique_upstream_data = list(set(upstream_dataset) - set(self._data))
        self._data += unique_upstream_data
        if self._auto_sync_flag in (True, "both", "upload_only"):
            self.upload()

    def _auto_sync(self):
        if self._auto_sync_flag in (True, "both", "download_only"):
            self.download()
        if self._auto_sync_flag in (True, "both", "upload_only"):
            self.upload()

    def sync(self):
        """
        Synchronize the dataset in both directions, downloading any values missing
        locally, and uploading any values missing from upstream in the account.
        """
        self.download()
        self.upload()

    def upstream_diff(self):
        """
        Prints the difference between the local dataset and the upstream dataset.
        """
        self._assert_name_exists()
        upstream_dataset = unify.download_dataset(self._name, api_key=self._api_key)
        upstream_set = set(upstream_dataset)
        local_set = set(self._data)
        unique_upstream_data = upstream_set - local_set
        print(
            "The following {} queries are stored upstream but not locally\n: "
            "{}".format(len(unique_upstream_data), unique_upstream_data)
        )
        unique_local_data = local_set - upstream_set
        print(
            "The following {} queries are stored upstream but not locally\n: "
            "{}".format(len(unique_local_data), unique_local_data)
        )
        self._auto_sync()

    def add(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                               List[Union[str, Dict, Prompt, Datum]]]):
        """
        Adds another dataset to this one, return a new Dataset instance, with this
        new dataset receiving all unique queries from the other added dataset.

        Args:
            other: The other dataset being added to this one.
        """
        other = other if isinstance(other, Dataset) else Dataset(other)
        data = list(dict.fromkeys(self._data + other._data))
        return Dataset(data=data, auto_sync=self._auto_sync_flag, api_key=self._api_key)

    def sub(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                               List[Union[str, Dict, Prompt, Datum]]]):
        """
        Subtracts another dataset from this one, return a new Dataset instance, with
        this new dataset losing all queries from the other subtracted dataset.

        Args:
            other: The other dataset being added to this one.
        """
        other = other if isinstance(other, Dataset) else Dataset(other)
        self_set = set(self._data)
        other_set = set(other)
        assert other_set <= self_set, (
            "cannot subtract dataset B from dataset A unless all queries of dataset "
            "B are also present in dataset A"
        )
        data = [item for item in self._data if item not in other]
        return Dataset(data=data, auto_sync=self._auto_sync_flag, api_key=self._api_key)

    def __iadd__(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                                    List[Union[str, Dict, Prompt, Datum]]]):
        """
        Adds another dataset to this one, with this dataset receiving all unique queries
        from the other added dataset.

        Args:
            other: The other dataset being added to this one.
        """
        other = other if isinstance(other, Dataset) else Dataset(other)
        self._data = list(dict.fromkeys(self._data + other._data))
        self._auto_sync()
        return self

    def __isub__(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                                    List[Union[str, Dict, Prompt, Datum]]]):
        """
        Subtracts another dataset from this one, with this dataset losing all queries
        from the other subtracted dataset.

        Args:
            other: The other dataset being added to this one.
        """
        other = other if isinstance(other, Dataset) else Dataset(other)
        self_set = set(self._data)
        other_set = set(other)
        assert other_set <= self_set, (
            "cannot subtract dataset B from dataset A unless all queries of dataset "
            "B are also present in dataset A"
        )
        self._data = [item for item in self._data if item not in other]
        self._auto_sync()
        return self

    def __add__(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                                   List[Union[str, Dict, Prompt, Datum]]]):
        return self.add(other)

    def __radd__(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                                    List[Union[str, Dict, Prompt, Datum]]]):
        return Dataset(other).add(self)

    def __sub__(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                                   List[Union[str, Dict, Prompt, Datum]]]):
        return self.sub(other)

    def __rsub__(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                                    List[Union[str, Dict, Prompt, Datum]]]):
        return Dataset(other).sub(self)

    def __iter__(self):
        self._auto_sync()
        for x in self._data:
            yield x

    def __getitem__(self, item):
        self._auto_sync()
        return self._data[item]

    def __rich_repr__(self):
        self._auto_sync()
        yield self._data
