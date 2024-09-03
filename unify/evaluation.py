from typing import Union, Optional

from unify.agent import Agent
from unify.dataset import Dataset
from unify.evaluator import Evaluator
from .utils.helpers import _validate_api_key


class Evaluation:
    # Constructors #
    # -------------#

    def __init__(
        self,
        agent: Union[Agent, str],
        dataset: Union[Dataset, str],
        evaluator: Union[Evaluator, str],
        auto_sync: bool = False,
        api_key: Optional[str] = None,
    ):
        """
        Initialize a local evaluation for a dataset of LLM queries.

        Args:
            agent: The agent that is being evaluated, either a local LLM agent or a
            string for an endpoint available in the platform.

            dataset: The dataset that the evaluation has been performed on.

            evaluator: The evaluator that has been judging the quality of responses.

            auto_sync: Whether to automatically keep this dataset fully synchronized
            with the upstream variant at all times.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.

        Raises:
            UnifyError: If the API key is missing.
        """
        self._agent = (
            agent
            if isinstance(agent, Agent)
            else Agent.from_upstream(agent, auto_sync, api_key)
        )
        self._dataset = (
            dataset
            if isinstance(dataset, Dataset)
            else Dataset.from_upstream(dataset, auto_sync, api_key)
        )
        self._evaluator = (
            evaluator
            if isinstance(evaluator, Evaluator)
            else Evaluator.from_upstream(evaluator, auto_sync, api_key)
        )
        self._auto_sync = auto_sync
        self._api_key = _validate_api_key(api_key)
        if self._auto_sync:
            self.sync()

    @staticmethod
    def from_upstream(
        agent: str,
        dataset: str,
        evaluator: str,
        auto_sync: bool = False,
        api_key: Optional[str] = None,
    ):
        """
        Initialize a local evaluation for a dataset of LLM queries.

        Args:
            agent: The agent that is being evaluated, either a local LLM agent or a
            string for an endpoint available in the platform.

            dataset: The dataset that the evaluation has been performed on.

            evaluator: The evaluator that has been judging the quality of responses.

            auto_sync: Whether to automatically keep this dataset fully synchronized
            with the upstream variant at all times.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.

        Raises:
            UnifyError: If the API key is missing.
        """
        return Evaluation(agent, dataset, evaluator, auto_sync, api_key)

    @staticmethod
    def from_file(
        filepath: str,
        agent: Union[Agent, str],
        evaluator: Union[Evaluator, str],
        auto_sync: bool = False,
        api_key: Optional[str] = None,
    ):
        """
        Loads the evaluation from a local .jsonl filepath.

        Args:
            filepath: Filepath (.jsonl) to load the dataset from.

            agent: The agent that is being evaluated, either a local LLM agent or a
            string for an endpoint available in the platform.

            evaluator: The evaluator that has been judging the quality of responses.

            auto_sync: Whether to automatically keep this dataset fully synchronized
            with the upstream variant at all times.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.
        """
        dataset = Dataset.from_file(filepath)
        return Evaluation(agent, dataset, evaluator, auto_sync, api_key)

    # Evaluation Triggering #
    # ----------------------#

    def evaluate(self):
        self._evaluator.evaluate(self._dataset, self._agent)
        if self._auto_sync:
            self._dataset.sync()

    # Dataset methods #
    # ----------------#

    def upload(self, overwrite=False):
        """
        Uploads all unique local data in the dataset evaluation to the user account
        upstream. This function will not download any uniques from upstream.
        Use `sync` to synchronize and superset the datasets in both directions.
        Set `overwrite=True` to disregard any pre-existing upstream data.

        Args:
            overwrite: Whether to overwrite the upstream dataset if it already exists
        """
        self._dataset.upload(overwrite)
        if self._auto_sync:
            self._dataset.sync()

    def download(self, overwrite=False):
        """
        Downloads all unique upstream data from the user account to the local dataset.
        This function will not upload any unique values stored locally.
        Use `sync` to synchronize and superset the datasets in both directions.
        Set `overwrite=True` to disregard any pre-existing data stored in this class.

        Args:
            overwrite: Whether to overwrite the local data, if any already exists
        """
        self._dataset.download(overwrite)
        if self._auto_sync:
            self._dataset.sync()

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
        self._dataset.upstream_diff()
        if self._auto_sync:
            self._dataset.sync()

    def save_to_file(self, filepath: str):
        """
        Saves to dataset to a local .jsonl filepath.

        Args:
            filepath: Filepath (.jsonl) to save the dataset to.
        """
        self._dataset.save_to_file(filepath)

    def add(self, other: __class__):
        """
        Adds another dataset to this one, return a new Dataset instance, with this
        new dataset receiving all unique queries from the other added dataset.

        Args:
            other: The other dataset being added to this one.
        """
        return self._dataset + other

    def sub(self, other: __class__):
        """
        Subtracts another dataset from this one, return a new Dataset instance, with
        this new dataset losing all queries from the other subtracted dataset.

        Args:
            other: The other dataset being added to this one.
        """
        return self._dataset - other

    def __iadd__(self, other):
        """
        Adds another dataset to this one, with this dataset receiving all unique queries
        from the other added dataset.

        Args:
            other: The other dataset being added to this one.
        """
        self._dataset += other
        if self._auto_sync:
            self._dataset.sync()

    def __isub__(self, other):
        """
        Subtracts another dataset from this one, with this dataset losing all queries
        from the other subtracted dataset.

        Args:
            other: The other dataset being added to this one.
        """
        self._dataset -= other
        if self._auto_sync:
            self._dataset.sync()

    def __add__(self, other):
        return self.add(other)

    def __sub__(self, other):
        return self.sub(other)

    def __repr__(self):
        raise NotImplementedError
