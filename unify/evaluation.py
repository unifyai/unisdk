from __future__ import annotations
import json
from enum import Enum
from typing import Union, Optional
from openai.types.chat.chat_completion import ChatCompletion

from unify.agent import Agent
from unify.types import DatasetEntry
from unify.dataset import Dataset
from unify.evaluator import Evaluator
from .utils.helpers import _validate_api_key
from unify.chat.clients.uni_llm import UniLLMClient


class Evaluation:

    def __init__(
        self,
        agent: Union[str, UniLLMClient, Agent],
        dataset: Union[str, Dataset],
        evaluator: Union[str, Evaluator],
        api_key: Optional[str] = None,
    ):
        """
        Initialize a local evaluation for a dataset of LLM queries.

        Args:
            agent: The agent that is being evaluated, either a local LLM agent or a
            string for an endpoint available in the platform.

            dataset: The dataset that the evaluation has been performed on.

            evaluator: The evaluator that has been judging the quality of responses.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.

        Raises:
            UnifyError: If the API key is missing.
        """
        # ToDo: support strings and upstream sync in this constructor
        self._agent = agent
        self._dataset = dataset
        self._evaluator = evaluator
        self._api_key = _validate_api_key(api_key)
        self._results = dict()

    def add_result(
            self,
            dataset_entry: DatasetEntry,
            score: Enum,
            response: Optional[ChatCompletion] = None
    ):
        key = json.dumps(dataset_entry.dict(exclude_none=True))
        self._results[key] = {"score": score, "response": response}
