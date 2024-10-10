from __future__ import annotations
from typing_extensions import Self
from pydantic import BaseModel
from typing import List, Dict, Union, Optional, Any

import unify
from unify.types import _Formatted
from unify.types import Prompt

# noinspection PyProtectedMember
from .utils.helpers import _validate_api_key, _dict_aligns_with_pydantic


class Dataset(_Formatted):

    def __init__(
        self,
        data: Union[str, Dict, Prompt, List[Union[str, Dict, Prompt]]],
        *,
        name: str = None,
        shared_data: Dict = None,
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

            shared_data: Data which is shared across all items in the dataset, with a
            nested structure following the nested structure of each dataset entry,
            in dictionary format.

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
        self._data = data
        self._api_key = _validate_api_key(api_key)
        self._shared_data = shared_data
        super().__init__()

    @property
    def name(self) -> str:
        """
        Name of the dataset.
        """
        return self._name

    def set_name(self, name: str) -> Self:
        """
        Set the name of the dataset.

        Args:
            name: The name to set the dataset to.

        Returns:
            This dataset, useful for chaining methods.
        """
        self._name = name
        return self

    @staticmethod
    def from_upstream(
        name: str,
        api_key: Optional[str] = None,
    ) -> Dataset:
        """
        Initialize a local dataset of LLM queries, from the upstream dataset.

        Args:
            name: The name of the dataset.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.

        Returns:
            The dataset, with contents downloaded from upstream.

        Raises:
            UnifyError: If the API key is missing.
        """
        data = unify.download_dataset(name, api_key=api_key)
        return Dataset(data, name=name, api_key=api_key)

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
        self._assert_name_exists()
        dataset_exists_upstream = self._name in unify.list_datasets(self._api_key)
        raw_data = [d.model_dump() for d in self._data]
        if overwrite:
            if dataset_exists_upstream:
                upstream_dataset = unify.download_dataset(
                    self._name, api_key=self._api_key
                )
                unique_upstream = [
                    item.model_dump()
                    for item in upstream_dataset
                    if item not in self._data
                ]
                unify.delete_data(self._name, unique_upstream)
                unify.add_data_by_value(self._name, raw_data)
            else:
                unify.upload_dataset_from_dictionary(self._name, raw_data)
        else:
            if dataset_exists_upstream:
                unify.add_data_by_value(self._name, raw_data)
            else:
                unify.upload_dataset_from_dictionary(self._name, raw_data)
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
        self._assert_name_exists()
        if overwrite:
            self._data = unify.download_dataset(self._name, api_key=self._api_key)
        else:
            upstream_dataset = unify.download_dataset(self._name, api_key=self._api_key)
            unique_local = [item for item in self._data if item not in upstream_dataset]
            self._data = upstream_dataset + unique_local
        return self

    def sync(self) -> Self:
        """
        Synchronize the dataset in both directions, downloading any values missing
        locally, and uploading any values missing from upstream in the account.

        Returns:
            This dataset after the in-place sync, useful for chaining methods.
        """
        self.download()
        self.upload()
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
        return self

    def add(
        self,
        other: Union[Dataset, str, Dict, Prompt, int, List[Union[str, Dict, Prompt]]],
    ) -> Self:
        """
        Adds another dataset to this one, return a new Dataset instance, with this
        new dataset receiving all unique queries from the other added dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            The new dataset following the addition.
        """
        if other == 0:
            return self
        other = other if isinstance(other, Dataset) else Dataset(other)
        data = list(dict.fromkeys(self._data + other._data))
        return Dataset(data=data, api_key=self._api_key)

    def sub(
        self, other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]]
    ) -> Self:
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
        return Dataset(data=data, api_key=self._api_key)

    def inplace_add(
        self,
        other: Union[Dataset, str, Dict, Prompt, int, List[Union[str, Dict, Prompt]]],
    ) -> Self:
        """
        Adds another dataset to this one, with this dataset receiving all unique queries
        from the other added dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            This dataset following the in-place addition.
        """
        if other == 0:
            return self
        other = other if isinstance(other, Dataset) else Dataset(other)
        self._data = list(dict.fromkeys(self._data + other._data))
        return self

    def inplace_sub(
        self, other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]]
    ) -> Self:
        """
        Subtracts another dataset from this one, with this dataset losing all queries
        from the other subtracted dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            This dataset following the in-place subtraction.
        """
        other = other if isinstance(other, Dataset) else Dataset(other)
        assert other in self, (
            "cannot subtract dataset B from dataset A unless all queries of dataset "
            "B are also present in dataset A"
        )
        self._data = [item for item in self._data if item not in other]
        return self

    def __add__(
        self, other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]]
    ) -> Self:
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

    def __radd__(
        self,
        other: Union[Dataset, str, Dict, Prompt, int, List[Union[str, Dict, Prompt]]],
    ) -> Self:
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
        if other == 0:
            return self
        return Dataset(other).add(self)

    def __iadd__(
        self, other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]]
    ) -> Self:
        """
        Adds another dataset to this one, with this dataset receiving all unique queries
        from the other added dataset.

        Args:
            other: The other dataset being added to this one.

        Returns:
            This dataset following the in-place addition.
        """
        return self.inplace_add(other)

    def __sub__(
        self, other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]]
    ) -> Self:
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

    def __rsub__(
        self, other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]]
    ) -> Self:
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
        self, other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]]
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

    def __iter__(self) -> Any:
        """
        Iterates through the dataset, return one instance at a time.

        Returns:
            The next instance in the dataset.
        """
        for x in self._data:
            yield x

    def __contains__(
        self, item: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]]
    ) -> bool:
        """
        Determine whether the item is contained within the dataset. The item is cast to
        a Dataset instance, and can therefore take on many different types. Only returns
        True if *all* entries in the passed dataset are contained within this dataset.

        Args:
            item: The item to cast to a Dataset before checking if it's a subset of this
            one.

        Returns:
            Boolean, whether the passed Dataset is a subset of this one.
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

    def __getitem__(self, item: Union[int, slice]) -> Union[Any, Dataset]:
        """
        Gets an item from the dataset, either via an int or slice. In the case of an
        int, then a data instance is returned, and for a slice a Dataset instance is
        returned.

        Args:
            item: integer or slice for extraction.

        Returns:
            An individual item or Dataset slice, for int and slice queries respectively.
        """
        if isinstance(item, int):
            return self._data[item]
        elif isinstance(item, slice):
            return Dataset(self._data[item.start : item.stop : item.step])
        raise TypeError(
            "expected item to be of type int or slice,"
            "but found {} of type {}".format(item, type(item))
        )

    # noinspection PyBroadException
    @staticmethod
    def _contains_chain(nest, chain, value):
        item = nest
        for idx in chain.split("/")[1:]:
            if isinstance(item, list) or isinstance(item, tuple):
                try:
                    idx = int(idx)
                    item = item[idx]
                except:
                    return False
            elif isinstance(item, dict):
                try:
                    item = item[idx]
                except:
                    return False
        return item == value

    def _shared_items_pruned(self, item, chain=""):
        if isinstance(item, list):
            ret = [
                v
                for v in [
                    self._shared_items_pruned(v, chain + "/" + str(i))
                    for i, v in enumerate(item)
                ]
                if v is not None
            ]
            return ret if bool(ret) else None
        elif isinstance(item, tuple):
            ret = (
                v
                for v in [
                    self._shared_items_pruned(v, chain + "/" + str(i))
                    for i, v in enumerate(item)
                ]
                if v is not None
            )
            return ret if bool(ret) else None
        elif isinstance(item, dict):
            ret = {
                k: v
                for k, v in {
                    k: self._shared_items_pruned(v, chain + "/" + str(k))
                    for k, v in item.items()
                }.items()
                if v is not None
            }
            return ret if bool(ret) else None
        elif isinstance(item, BaseModel):
            dct = {
                k: v
                for k, v in {
                    k: self._shared_items_pruned(v, chain + "/" + str(k))
                    for k, v in item.model_dump().items()
                }.items()
                if v is not None
            }
            if dct == {}:
                return None
            return self._create_pydantic_model(item, dct)
        elif self._contains_chain(self._shared_data, chain, item):
            return None
        else:
            return item

    def __rich_repr__(self) -> List[Any]:
        """
        Used by the rich package for representing and print the instance.
        """
        if self._shared_data is None:
            yield self._data
        else:
            yield "shared", self._prune(
                self._create_pydantic_model(self._data[0], self._shared_data)
            )
            yield [self._shared_items_pruned(d) for d in self._data]
