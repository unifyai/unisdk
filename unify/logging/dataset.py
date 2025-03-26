from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Dict, List, Optional, Union

import unify
from typing_extensions import Self

from ..universal_api.types import Prompt

# noinspection PyProtectedMember
from ..utils.helpers import _validate_api_key


def _to_raw_data(x: Dict[str, Any]):
    return x["data"] if "data" in x and len(x) == 1 else x


class Dataset(Sequence):
    def __init__(
        self,
        data: Optional[Any] = None,
        *,
        name: str = None,
        allow_duplicates: bool = False,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Initialize a local dataset.

        Args:
            data: The data for populating the dataset.
            This needs to be a list of JSON serializable objects.

            name: The name of the dataset. To create a dataset for a specific project
            with name {project_name}, then prefix the name with {project_name}/{name}.

            allow_duplicates: Whether to allow duplicates in the dataset.

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
        self._allow_duplicates = allow_duplicates
        self._api_key = _validate_api_key(api_key)
        self._logs = [
            (
                entry
                if isinstance(entry, unify.Log)
                else unify.Log(
                    **(entry if isinstance(entry, dict) else {"data": entry}),
                )
            )
            for entry in data
        ]
        super().__init__()

    @property
    def name(self) -> str:
        """
        Name of the dataset.
        """
        return self._name

    @property
    def allow_duplicates(self) -> bool:
        """
        Whether to allow duplicates in the dataset.
        """
        return self._allow_duplicates

    @property
    def data(self):
        """
        Dataset entries.
        """
        return [_to_raw_data(l.entries) for l in self._logs]

    def _set_data(self, data):
        self._logs = [
            unify.Log(**(entry if isinstance(entry, dict) else {"data": entry}))
            for entry in data
        ]

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

    def set_allow_duplicates(self, allow_duplicates: bool) -> Self:
        """
        Set whether to allow duplicates in the dataset.

        Args:
            allow_duplicates: Whether to allow duplicates in the dataset.

        Returns:
            This dataset, useful for chaining methods.
        """
        self._allow_duplicates = allow_duplicates
        return self

    @staticmethod
    def from_upstream(
        name: str,
        api_key: Optional[str] = None,
    ) -> Dataset:
        """
        Initialize a local dataset from the upstream dataset.

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
        data = unify.download_dataset(name=name, api_key=api_key)
        return Dataset(
            data,
            name=name,
            api_key=api_key,
        )

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
        dataset_ids = unify.upload_dataset(
            name=self._name,
            data=self._logs,
            overwrite=overwrite,
            allow_duplicates=self._allow_duplicates,
        )
        assert len(dataset_ids) >= len(
            self._logs,
        ), "Number of upstream items must be greater than or equal to items"
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

        if f"Datasets/{self._name}" not in unify.get_contexts():
            upstream_dataset = list()
        else:
            upstream_dataset = unify.download_dataset(
                name=self._name,
                api_key=self._api_key,
            )
        if overwrite:
            self._logs = upstream_dataset
            return self
        if self._allow_duplicates:
            local_ids = set([l.id for l in self._logs if l.id is not None])
            new_data = [l for l in upstream_dataset if l.id not in local_ids]
        else:
            local_vals_to_logs = {json.dumps(l.entries): l for l in self._logs}
            local_values = set([json.dumps(l.entries) for l in self._logs])
            upstream_values = set()
            new_data = list()
            for l in upstream_dataset:
                uid = l.id
                value = json.dumps(l.entries)
                if value not in local_values.union(upstream_values):
                    new_data.append(l)
                    upstream_values.add(value)
                elif value in local_vals_to_logs:
                    local_log = local_vals_to_logs[value]
                    if local_log.id != uid:
                        local_log.set_id(uid)

        self._logs += new_data
        return self

    def sync(self) -> Self:
        """
        Synchronize the dataset in both directions, downloading any values missing
        locally, and uploading any values missing from upstream in the account.

        Returns:
            This dataset after the in-place sync, useful for chaining methods.
        """
        self.upload()
        self.download(overwrite=True)
        return self

    def upstream_diff(self) -> Self:
        """
        Prints the difference between the local dataset and the upstream dataset.

        Returns:
            This dataset after printing the diff, useful for chaining methods.
        """
        self._assert_name_exists()
        upstream_dataset = unify.download_dataset(
            name=self._name,
            api_key=self._api_key,
        )
        unique_upstream = [
            item["entry"] for item in upstream_dataset if item["entry"] not in self.data
        ]
        print(
            "The following {} entries are stored upstream but not locally\n: "
            "{}".format(len(unique_upstream), unique_upstream),
        )
        unique_local = [item for item in self.data if item not in upstream_dataset]
        print(
            "The following {} entries are stored upstream but not locally\n: "
            "{}".format(len(unique_local), unique_local),
        )
        return self

    def add(
        self,
        other: Union[
            Dataset,
            str,
            Dict,
            Prompt,
            int,
            List[Union[str, Dict, Prompt]],
        ],
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
        data = self.data + [d for d in other.data if d not in self.data]
        return Dataset(data=data, api_key=self._api_key)

    def sub(
        self,
        other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]],
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
        data = [item for item in self.data if item not in other]
        return Dataset(data=data, api_key=self._api_key)

    def inplace_add(
        self,
        other: Union[
            Dataset,
            str,
            Dict,
            Prompt,
            int,
            List[Union[str, Dict, Prompt]],
        ],
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
        self._logs = self._logs + [d for d in other._logs if d not in self._logs]
        return self

    def inplace_sub(
        self,
        other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]],
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
        self._logs = [item for item in self._logs if item not in other]
        return self

    def __add__(
        self,
        other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]],
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
        other: Union[
            Dataset,
            str,
            Dict,
            Prompt,
            int,
            List[Union[str, Dict, Prompt]],
        ],
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
        self,
        other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]],
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
        self,
        other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]],
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
        self,
        other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]],
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
        self,
        other: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]],
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
        for l in self._logs:
            yield l

    def __contains__(
        self,
        item: Union[Dataset, str, Dict, Prompt, List[Union[str, Dict, Prompt]]],
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
        this_serialized = [
            json.dumps(
                {
                    k: v
                    for k, v in l.to_json().items()
                    if k not in ("id", "ts") and v not in ({}, None)
                },
            )
            for l in self._logs
        ]
        item_serialized = [
            json.dumps(
                {
                    k: v
                    for k, v in l.to_json().items()
                    if k not in ("id", "ts") and v not in ({}, None)
                },
            )
            for l in item._logs
        ]
        this_set = set(this_serialized)
        combined_set = set(this_serialized + item_serialized)
        return len(this_set) == len(combined_set)

    def __len__(self) -> int:
        """
        Returns the number of entries contained within the dataset.

        Returns:
            The number of entries in the dataset.
        """
        return len(self._logs)

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
            return self._logs[item]
        elif isinstance(item, slice):
            return Dataset(self._logs[item.start : item.stop : item.step])
        raise TypeError(
            "expected item to be of type int or slice,"
            "but found {} of type {}".format(item, type(item)),
        )

    def __setitem__(self, item: Union[int, slice], value: Union[Any, Dataset]):
        if isinstance(item, int):
            if isinstance(value, unify.Log):
                self._logs[item] = value
            else:
                self._logs[item] = unify.Log(
                    **(value if isinstance(value, dict) else {"data": value}),
                )
        elif isinstance(item, slice):
            self._logs[item.start : item.stop : item.step] = [
                (
                    unify.Log(**(v if isinstance(v, dict) else {"data": v}))
                    if not isinstance(v, unify.Log)
                    else v
                )
                for v in value
            ]
        else:
            raise TypeError(
                "expected item to be of type int or slice,",
            )

    def __repr__(self):
        return f"unify.Dataset({self.data}, name='{self._name}')"
