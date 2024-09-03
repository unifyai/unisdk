import unify
import jsonlines
from typing import List, Dict, Any, Union, Optional
from openai.types.chat.chat_completion import ChatCompletion
from .utils.helpers import _validate_api_key


class Dataset:
    def __init__(
        self,
        name: str = None,
        queries: List[Union[str, ChatCompletion]] = None,
        extra_fields: Dict[str, List[Any]] = None,
        data: List[Dict[str, Union[ChatCompletion, Any]]] = None,
        auto_sync: bool = False,
        api_key: Optional[str] = None,
    ):
        """
        Initialize a local dataset of LLM queries.

        Args:
            name: The name of the dataset.

            queries: List of LLM queries to initialize the dataset with.

            extra_fields: Dictionary of lists for arbitrary extra fields contained
            within the dataset.

            data: If neither `queries` nor `extra_fields` are specified, then this can
            be specified instead, which is simply a list of dicts with each first key as
            "query" and all other keys otherwise coming from the `extra_fields`. This is
            the internal representation used by the class.

            auto_sync: Whether to automatically keep this dataset fully synchronized
            with the upstream variant at all times.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.

        Raises:
            UnifyError: If the API key is missing.
        """
        self._name = name
        assert (
            queries is None and extra_fields is None
        ) or data is None, (
            "if data is specified, then both queries and extra_fields must be None"
        )
        if data is not None:
            self._data = data
        else:
            queries = [] if queries is None else queries
            # ToDo: create ChatCompletion objects for any strings passed
            extra_fields = {} if extra_fields is None else extra_fields
            num_items = len(queries)
            data_as_dict = dict(**{"query": v for v in queries}, **extra_fields)
            self._data = [
                {k: v[i] for k, v in data_as_dict.items()} for i in range(num_items)
            ]
        self._api_key = _validate_api_key(api_key)
        self._auto_sync = auto_sync
        if self._auto_sync:
            self.sync()

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
        return Dataset(name, data=data, auto_sync=auto_sync, api_key=api_key)

    @staticmethod
    def from_file(
        filepath: str,
        name: str = None,
        auto_sync: bool = False,
        api_key: Optional[str] = None,
    ):
        """
        Loads the dataset from a local .jsonl filepath.

        Args:
            filepath: Filepath (.jsonl) to load the dataset from.

            name: The name of the dataset.

            auto_sync: Whether to automatically keep this dataset fully synchronized
            with the upstream variant at all times.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.
        """
        with jsonlines.open(filepath, mode="r") as reader:
            data = reader.read()
        return Dataset(name, data=data, auto_sync=auto_sync, api_key=api_key)

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
        if overwrite:
            if self._name in unify.list_datasets(self._api_key):
                unify.delete_dataset(self._name, self._api_key)
            unify.upload_dataset_from_dictionary(self._name, self._data)
            return
        upstream_dataset = unify.download_dataset(self._name, api_key=self._api_key)
        unique_local_data = list(set(self._data) - set(upstream_dataset))
        unify.append_to_dataset_from_dictionary(self._name, unique_local_data)
        if self._auto_sync:
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
        if self._auto_sync:
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
        if self._auto_sync:
            self.sync()

    def save_to_file(self, filepath: str):
        """
        Saves to dataset to a local .jsonl filepath.

        Args:
            filepath: Filepath (.jsonl) to save the dataset to.
        """
        with jsonlines.open(filepath, mode="w") as writer:
            writer.write_all(self._data)
        if self._auto_sync:
            self.sync()

    def add(self, other: __class__):
        """
        Adds another dataset to this one, return a new Dataset instance, with this
        new dataset receiving all unique queries from the other added dataset.

        Args:
            other: The other dataset being added to this one.
        """
        data = list(set(self._data + other))
        return Dataset(data=data, auto_sync=self._auto_sync, api_key=self._api_key)

    def sub(self, other: __class__):
        """
        Subtracts another dataset from this one, return a new Dataset instance, with
        this new dataset losing all queries from the other subtracted dataset.

        Args:
            other: The other dataset being added to this one.
        """
        self_set = set(self._data)
        other_set = set(other)
        assert other_set <= self_set, (
            "cannot subtract dataset B from dataset A unless all queries of dataset "
            "B are also present in dataset A"
        )
        data = list(self_set - other_set)
        return Dataset(data=data, auto_sync=self._auto_sync, api_key=self._api_key)

    def __iadd__(self, other):
        """
        Adds another dataset to this one, with this dataset receiving all unique queries
        from the other added dataset.

        Args:
            other: The other dataset being added to this one.
        """
        self._data = list(set(self._data + other))
        if self._auto_sync:
            self.sync()

    def __isub__(self, other):
        """
        Subtracts another dataset from this one, with this dataset losing all queries
        from the other subtracted dataset.

        Args:
            other: The other dataset being added to this one.
        """
        self_set = set(self._data)
        other_set = set(other)
        assert other_set <= self_set, (
            "cannot subtract dataset B from dataset A unless all queries of dataset "
            "B are also present in dataset A"
        )
        self._data = list(self_set - other_set)
        if self._auto_sync:
            self.sync()

    def __add__(self, other):
        return self.add(other)

    def __sub__(self, other):
        return self.sub(other)

    def __repr__(self):
        raise NotImplementedError
