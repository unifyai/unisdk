from __future__ import annotations
from typing_extensions import Self
from typing import List, Dict, Union, Optional

import unify
from unify.casting import cast
from unify.types import _Formatted
from unify.types import Prompt, Datum
# noinspection PyProtectedMember
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
    ) -> None:
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
            will be bi-directional, if "upload" then all local changes will be
            uploaded to the upstream account without any downloads, if "download"
            then all upstream changes will be downloaded locally without any uploads.
            If "upstream_mirrors_local" then the upstream dataset will be anchored to
            the local version at all times, and any other uploads outside the local
            dataset will be overwritten. If "local_mirrors_upstream" then the local
            version will be anchored to the upstream version at all times, and any local
            changes will be overwritten. If `False` or "neither" then no synchronization
            will be done automatically.

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
            self._data = [cast(usr_msg, Datum) for usr_msg in data]
        elif isinstance(data[0], Prompt):
            self._data = [cast(prompt, Datum) for prompt in data]
        elif isinstance(data[0], dict) and _dict_aligns_with_pydantic(data[0], Prompt):
            self._data = [cast(Prompt(**dct), Datum) for dct in data]
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
        """
        Name of the dataset.
        """
        self._auto_sync()
        return self._name

    @property
    def auto_sync(self) -> Union[bool, str]:
        """
        The auto-sync mode currently selected.
        This dictates whether to automatically keep this dataset fully synchronized
        with the upstream variant at all times. If `True` or "both" then the sync
        will be bi-directional, if "upload" then all local changes will be
        uploaded to the upstream account without any downloads, if "download"
        then all upstream changes will be downloaded locally without any uploads.
        If "upstream_mirrors_local" then the upstream dataset will be anchored to the
        local version at all times, and any other uploads outside the local dataset
        will be overwritten. If "local_mirrors_upstream" then the local version will be
        anchored to the upstream version at all times, and any local changes will be
        overwritten. If `False` or "neither" then no synchronization will be done
        automatically.
        """
        self._auto_sync()
        return self._auto_sync_flag

    def set_name(self, name: str) -> Self:
        """
        Set the name of the dataset.

        Args:
            name: The name to set the dataset to.

        Returns:
            This dataset, useful for chaining methods.
        """
        self._auto_sync()
        self._name = name
        return self

    def set_auto_sync(self, auto_sync: Union[bool, str]) -> Self:
        """
        Set the value of the auto-sync flag.

        Args:
            auto_sync: Whether to automatically keep this dataset fully synchronized
            with the upstream variant at all times. If `True` or "both" then the sync
            will be bi-directional, if "upload" then all local changes will be
            uploaded to the upstream account without any downloads, if "download"
            then all upstream changes will be downloaded locally without any uploads.
            If "upstream_mirrors_local" then the upstream dataset will be anchored to
            the local version at all times, and any other uploads outside the local
            dataset will be overwritten. If "local_mirrors_upstream" then the local
            version will be anchored to the upstream version at all times, and any local
            changes will be overwritten. If `False` or "neither" then no synchronization
            will be done automatically.

        Returns:
            This dataset, useful for chaining methods.
        """
        self._auto_sync()
        self._auto_sync_flag = auto_sync
        return self

    @staticmethod
    def from_upstream(
        name: str,
        auto_sync: Union[bool, str] = False,
        api_key: Optional[str] = None,
    ) -> Self:
        """
        Initialize a local dataset of LLM queries, from the upstream dataset.

        Args:
            name: The name of the dataset.

            auto_sync: Whether to automatically keep this dataset fully synchronized
            with the upstream variant at all times.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.

        Returns:
            The dataset, with contents downloaded from upstream.

        Raises:
            UnifyError: If the API key is missing.
        """
        data = unify.download_dataset(name, api_key=api_key)
        return Dataset(data, name=name, auto_sync=auto_sync, api_key=api_key)

    def _assert_name_exists(self) -> None:
        assert self._name is not None, (
            "Dataset name must be specified in order to upload, download, sync or "
            "compare to a corresponding dataset in your upstream account. "
            "You can simply use .set_name() and set it to the same name as your "
            "upstream dataset, or create a new name if it doesn't yet exist upstream."
        )

    def upload(self, overwrite: bool = False) -> Self:
        """
        Uploads all unique local data in the dataset to the user account upstream.
        This function will not download any uniques from upstream.
        Use `sync` to synchronize and superset the datasets in both directions.
        Set `overwrite=True` to disregard any pre-existing upstream data.

        Args:
            overwrite: Whether to overwrite the upstream dataset if it already exists.

        Returns:
            This dataset, useful for chaining methods.
        """
        if self._auto_sync_flag == "local_mirrors_upstream":
            raise Exception("upload not permitted when local mirrors upstream")
        self._assert_name_exists()
        dataset_exists_upstream = self._name in unify.list_datasets(self._api_key)
        if overwrite:
            if dataset_exists_upstream:
                upstream_dataset = unify.download_dataset(
                    self._name, api_key=self._api_key
                )
                unique_upstream = [item.dict() for item in upstream_dataset
                                   if item not in self._data]
                unify.delete_data(self._name, unique_upstream)
                unique_local = [item.dict() for item in self._data
                                if item not in upstream_dataset]
                unify.add_data(self._name, unique_local)
            else:
                data = [datum.dict() for datum in self._data]
                unify.upload_dataset_from_dictionary(self._name, data)
        else:
            if dataset_exists_upstream:
                upstream_dataset = unify.download_dataset(
                    self._name, api_key=self._api_key
                )
                unique_local = [item.dict() for item in self._data
                                if item not in upstream_dataset]
                unify.add_data(self._name, unique_local)
            else:
                unique_local = [entry.dict() for entry in self._data]
                unify.upload_dataset_from_dictionary(self._name, unique_local)
        if self._auto_sync_flag in (True, "both", "download", "local_mirrors_upstream"):
            auto_sync_flag = self._auto_sync_flag
            self._auto_sync_flag = False
            overwrite = True if auto_sync_flag == "local_mirrors_upstream" else False
            self.download(overwrite=overwrite)
            self._auto_sync_flag = auto_sync_flag
        return self

    def download(self, overwrite: bool = False) -> Self:
        """
        Downloads all unique upstream data from the user account to the local dataset.
        This function will not upload any unique values stored locally.
        Use `sync` to synchronize and superset the datasets in both directions.
        Set `overwrite=True` to disregard any pre-existing data stored in this class.

        Args:
            overwrite: Whether to overwrite the local data, if any already exists

        Returns:
            This dataset after the in-place download, useful for chaining methods.
        """
        if self._auto_sync_flag == "upstream_mirrors_local":
            raise Exception("download not permitted when upstream mirrors local")
        self._assert_name_exists()
        if overwrite:
            self._data = unify.download_dataset(self._name, api_key=self._api_key)
        else:
            upstream_dataset = unify.download_dataset(
                self._name, api_key=self._api_key
            )
            unique_local = [item for item in self._data if item not in upstream_dataset]
            self._data = upstream_dataset + unique_local
        if self._auto_sync_flag in (True, "both", "upload", "upstream_mirrors_local"):
            auto_sync_flag = self._auto_sync_flag
            self._auto_sync_flag = False
            overwrite = True if auto_sync_flag == "upstream_mirrors_local" else False
            self.upload(overwrite=overwrite)
            self._auto_sync_flag = auto_sync_flag
        return self

    def _auto_sync(self) -> None:
        if self._auto_sync_flag in (True, "both", "download", "local_mirrors_upstream"):
            auto_sync_flag = self._auto_sync_flag
            self._auto_sync_flag = False
            overwrite = True if auto_sync_flag == "local_mirrors_upstream" else False
            self.download(overwrite=overwrite)
            self._auto_sync_flag = auto_sync_flag
        if self._auto_sync_flag in (True, "both", "upload", "upstream_mirrors_local"):
            auto_sync_flag = self._auto_sync_flag
            self._auto_sync_flag = False
            overwrite = True if auto_sync_flag == "upstream_mirrors_local" else False
            self.upload(overwrite=overwrite)
            self._auto_sync_flag = auto_sync_flag

    def sync(self) -> Self:
        """
        Synchronize the dataset in both directions, downloading any values missing
        locally, and uploading any values missing from upstream in the account.

        Returns:
            This dataset after the in-place sync, useful for chaining methods.
        """
        auto_sync_flag = self._auto_sync_flag
        self._auto_sync_flag = False
        self.download()
        self.upload()
        self._auto_sync_flag = auto_sync_flag
        return self

    def upstream_diff(self) -> Self:
        """
        Prints the difference between the local dataset and the upstream dataset.

        Returns:
            This dataset after printing the diff, useful for chaining methods.
        """
        self._assert_name_exists()
        upstream_dataset = unify.download_dataset(self._name, api_key=self._api_key)
        unique_upstream = [item for item in upstream_dataset if item not in self._data]
        print(
            "The following {} queries are stored upstream but not locally\n: "
            "{}".format(len(unique_upstream), unique_upstream)
        )
        unique_local = [item for item in self._data if item not in upstream_dataset]
        print(
            "The following {} queries are stored upstream but not locally\n: "
            "{}".format(len(unique_local), unique_local)
        )
        self._auto_sync()
        return self

    def add(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                               List[Union[str, Dict, Prompt, Datum]]]) -> Self:
        """
        Adds another dataset to this one, return a new Dataset instance, with this
        new dataset receiving all unique queries from the other added dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            The new dataset following the addition.
        """
        other = other if isinstance(other, Dataset) else Dataset(other)
        data = list(dict.fromkeys(self._data + other._data))
        return Dataset(data=data, auto_sync=self._auto_sync_flag, api_key=self._api_key)

    def sub(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                               List[Union[str, Dict, Prompt, Datum]]]) -> Self:
        """
        Subtracts another dataset from this one, return a new Dataset instance, with
        this new dataset losing all queries from the other subtracted dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            The new dataset following the subtraction.
        """
        other = other if isinstance(other, Dataset) else Dataset(other)
        assert other in self, (
            "cannot subtract dataset B from dataset A unless all queries of dataset "
            "B are also present in dataset A"
        )
        data = [item for item in self._data if item not in other]
        return Dataset(data=data, auto_sync=self._auto_sync_flag, api_key=self._api_key)

    def inplace_add(
            self,
            other: Union[Dataset, str, Dict, Prompt, Datum,
                         List[Union[str, Dict, Prompt, Datum]]]
    ) -> Self:
        """
        Adds another dataset to this one, with this dataset receiving all unique queries
        from the other added dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            This dataset following the in-place addition.
        """
        if self._auto_sync_flag == "local_mirrors_upstream":
            raise TypeError("Adding entries not permitted when local mirrors upstream")
        other = other if isinstance(other, Dataset) else Dataset(other)
        self._data = list(dict.fromkeys(self._data + other._data))
        self._auto_sync()
        return self

    def inplace_sub(
            self,
            other: Union[Dataset, str, Dict, Prompt, Datum,
                         List[Union[str, Dict, Prompt, Datum]]]
    ) -> Self:
        """
        Subtracts another dataset from this one, with this dataset losing all queries
        from the other subtracted dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            This dataset following the in-place subtraction.
        """
        if self._auto_sync_flag == "local_mirrors_upstream":
            raise TypeError("Adding entries not permitted when local mirrors upstream")
        other = other if isinstance(other, Dataset) else Dataset(other)
        assert other in self, (
            "cannot subtract dataset B from dataset A unless all queries of dataset "
            "B are also present in dataset A"
        )
        self._data = [item for item in self._data if item not in other]
        self._auto_sync()
        return self

    def __add__(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                                   List[Union[str, Dict, Prompt, Datum]]]) -> Self:
        """
        Adds another dataset to this one via the + operator, return a new Dataset
        instance, with this new dataset receiving all unique queries from the other
        added dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            The new dataset following the addition.
        """
        return self.add(other)

    def __radd__(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                                    List[Union[str, Dict, Prompt, Datum]]]) -> Self:
        """
        Adds another dataset to this one via the + operator, this is used if the
        other item does not have a valid __add__ method for these two types. Return a
        new Dataset instance, with this new dataset receiving all unique queries from
        the other added dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            The new dataset following the addition.
        """
        return Dataset(other).add(self)

    def __iadd__(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                                    List[Union[str, Dict, Prompt, Datum]]]) -> Self:
        """
        Adds another dataset to this one, with this dataset receiving all unique queries
        from the other added dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            This dataset following the in-place addition.
        """
        return self.inplace_add(other)

    def __sub__(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                                   List[Union[str, Dict, Prompt, Datum]]]) -> Self:
        """
        Subtracts another dataset from this one via the - operator, return a new Dataset
        instance, with this new dataset losing all queries from the other subtracted
        dataset.

        Args:
            other: The other dataset being subtracted from this one.

        Returns:
            The new dataset following the subtraction.
        """
        return self.sub(other)

    def __rsub__(self, other: Union[Dataset, str, Dict, Prompt, Datum,
                                    List[Union[str, Dict, Prompt, Datum]]]) -> Self:
        """
        Subtracts another dataset from this one via the - operator, this is used if the
        other item does not have a valid __sub__ method for these two types. Return a
        new Dataset instance, with this new dataset losing all queries from the other
        subtracted dataset.

        Args:
            other: The other dataset being subtracted from this one.

        Returns:
            The new dataset following the subtraction.
        """
        return Dataset(other).sub(self)

    def __isub__(
            self,
            other: Union[Dataset, str, Dict, Prompt, Datum,
                         List[Union[str, Dict, Prompt, Datum]]]
    ) -> Self:
        """
        Subtracts another dataset from this one, with this dataset losing all queries
        from the other subtracted dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            This dataset following the in-place subtraction.
        """
        return self.inplace_sub(other)

    def __iter__(self) -> Datum:
        """
        Iterates through the dataset, return one Datum instance at a time.

        Returns:
            A Datum instance per iteration.
        """
        self._auto_sync()
        for x in self._data:
            yield x

    def __contains__(self, item: Union[Dataset, str, Dict, Prompt, Datum,
                                       List[Union[str, Dict, Prompt, Datum]]]) -> bool:
        """
        Determine whether the item is contained within the dataset. The item is cast to
        a Dataset instance, and can therefore take on many different types. Only returns
        True if *all* entries in the passed dataset are contained within this dataset.

        Args:
            item: The item to cast to a Dataset before checking if it's a subset of this
            one.

        Returns:
            Boolean, as to whether or not the passed Dataset is a subset of this one.
        """
        item = item if isinstance(item, Dataset) else Dataset(item)
        this_set = set(self._data)
        combined_set = set(self._data + item._data)
        return len(this_set) == len(combined_set)

    def __len__(self) -> int:
        """
        Returns the number of entries contained within the dataset.

        Returns:
            The number of entries in the dataset.
        """
        return len(self._data)

    def __getitem__(self, item: Union[int, slice]) -> Union[Datum, Dataset]:
        """
        Gets an item from the dataset, either via an int or slice. In the case of an
        int then a Datum instance is returned, and for a slice a Dataset instance is
        returned.

        Args:
            item: integer or slice for extraction.

        Returns:
            A Datum or Dataset instance, for int and slice queries respectively.
        """
        self._auto_sync()
        if isinstance(item, int):
            return self._data[item]
        elif isinstance(item, slice):
            return Dataset(self._data[item.start:item.stop:item.step])
        raise TypeError("expected item to be of type int or slice,"
                        "but found {} of type {}".format(item, type(item)))

    def __rich_repr__(self) -> List[Datum]:
        """
        Used by the rich package for representing and print the instance.
        """
        self._auto_sync()
        yield self._data
