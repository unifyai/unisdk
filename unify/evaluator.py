import abc
from abc import abstractmethod
from typing import Union

from unify.dataset import Dataset
from unify.agent import Agent
from unify.types import Prompt
from unify.chat.clients.uni_llm import UniLLMClient


class Evaluator(abc.ABC):

    @abstractmethod
    def evaluate(
            self,
            agent: Union[str, UniLLMClient, Agent],
            dataset: Union[str, Dataset],
            default_prompt: Prompt = None,
    ):
        """
        Evaluate the agent on the given dataset, based on this evaluator.

        Args:
            agent: Name of the endpoint or handle to the local Agent (possibly
            multi-step LLM calls) to evaluate.

            dataset: Name of the uploaded dataset or handle to the local Dataset
            instance to evaluate

            default_prompt: The default prompt for evaluation, which each unique query in
            the dataset will inherit from, overwriting the extra fields. This prompt can
            therefore include temperature, system message, tools etc. which are not
            present in each prompt in the dataset.
        """
        raise NotImplementedError


# class LLMJudge(Evaluator):
#
#     def __init__(
#             self,
#             system_message: str = None,
#             class_config: List[Dict[str, Union[float, str]]] = None,
#             judge_models: Union[str, List[str]] = None,
#             name: str = None,
#             previous_version: Evaluator = None,
#             auto_sync: bool = False,
#             api_key: Optional[str] = None,
#             client: Client = None,
#     ):
#         """
#         Initialize an LLM as a judge (or jury) evaluator.
#
#         Args:
#             system_message: An optional custom system message to provide specific
#             instructions to the judge on how to score the answers.
#
#             class_config: If set, describes the list of classifications that the LLM
#              judge(s) use(s) to score each prompt. For example:
#             ```
#             [{"label": "Excellent", "score": 1.0, "description": "A perfect answer
#             with no factual mistakes"},
#             {"label": "Good", "score": 0.5, "description": "An average answer"},
#             {"label": "Bad", "score": 0.0, "description": "An incorrect answer,
#             containing a significant factual mistake"}]
#             ```
#
#             judge_models: Specifies the LLM(s) to be used as the judge. This can be a
#             string containing a single model name or a list of model names. If
#             unspecified then `claude-3.5-sonnet@aws-bedrock` is used.
#
#             name: The name of the evaluator.
#
#             previous_version: Specifies the previous version of the LLM Judge evaluator
#             if one exists. Otherwise it should be set as None if this is the first
#             iteration of the judge.
#
#             auto_sync: Whether to automatically keep this dataset fully synchronized
#             with the upstream variant at all times.
#
#             api_key: API key for accessing the Unify API. If None, it attempts to
#             retrieve the API key from the environment variable UNIFY_KEY. Defaults to
#             None.
#
#             client: Unify client which is connected to the chat completions API.
#
#         Raises:
#             UnifyError: If the API key is missing.
#         """
#         self._name = name
#         self._system_message = system_message
#         self._class_config = class_config
#         self._judge_models = judge_models
#         self._previous_version = previous_version
#         self._auto_sync = auto_sync
#         self._api_key = _validate_api_key(api_key)
#         self._client = client if client is not None else Unify(api_key=self._api_key)
#         if self._auto_sync:
#             self.sync()
#
#     @staticmethod
#     def from_upstream(
#             name: str,
#             api_key: Optional[str] = None,
#     ):
#         """
#         Initialize a local LLM Judge evaluator, from the upstream evaluator config.
#
#         Args:
#             name: The name of the LLM judge evaluator.
#
#             api_key: API key for accessing the Unify API. If None, it attempts to
#             retrieve the API key from the environment variable UNIFY_KEY. Defaults to
#             None.
#
#         Raises:
#             UnifyError: If the API key is missing.
#         """
#         config = unify.utils.get_evaluator(name, api_key=api_key)
#         return LLMJudge(
#             name,
#             config.system_message,
#             config.class_config,
#             config.judge_models,
#             api_key=api_key
#         )
#
#     def update(
#             self,
#             system_message: str = None,
#             class_config: List[Dict[str, Union[float, str]]] = None,
#             judge_models: Union[str, List[str]] = None,
#     ):
#         """
#         Creates a new version of the evaluator and increments the version number, whilst
#         maintaining a reference to the old evaluator.
#
#         system_message: An optional custom system message to provide specific
#         instructions to the judge on how to score the answers.
#
#         class_config: If set, describes the list of classifications that the LLM
#          judge(s) use(s) to score each prompt. For example:
#         ```
#         [{"label": "Excellent", "score": 1.0, "description": "A perfect answer
#         with no factual mistakes"},
#         {"label": "Good", "score": 0.5, "description": "An average answer"},
#         {"label": "Bad", "score": 0.0, "description": "An incorrect answer,
#         containing a significant factual mistake"}]
#         ```
#
#         judge_models: Specifies the LLM(s) to be used as the judge. This can be a
#         string containing a single model name or a list of model names. If
#         unspecified then `claude-3.5-sonnet@aws-bedrock` is used.
#         """
#         sm_changed = system_message not in (None, self._system_message)
#         cc_changed = class_config not in (None, self._class_config)
#         jm_changed = judge_models not in (None, self._judge_models)
#
#         assert sm_changed or cc_changed or jm_changed,\
#             "At least one of `system_message`, `class_config` or `judge_models` must " \
#             "be changed when calling `update`"
#
#         split_name = self._name.split("_")
#         suffix = split_name[-1]
#         if len(suffix) >= 2 and suffix[0] == "v" and suffix[1:].isdigit():
#             new_version = int(suffix[1:]) + 1
#             new_name = "_".join(split_name[:-1] + ["v{}".format(new_version)])
#         else:
#             new_name = self._name + "_v0"
#         return LLMJudge(
#             new_name,
#             system_message,
#             class_config,
#             judge_models,
#             self,
#             self._auto_sync,
#             self._api_key
#         )
#
#     def upload(self, overwrite=False):
#         """
#         Uploads the evaluator to the user account upstream. Set `overwrite=True` to
#         overwrite the evaluator if it already exists upstream.
#
#         Args:
#             overwrite: Whether to overwrite the upstream dataset if it already exists
#         """
#         if self._name in unify.utils.list_evaluators(self._api_key):
#             if overwrite:
#                 unify.utils.delete_evaluator(self._name, self._api_key)
#             else:
#                 raise Exception("Evaluator with name {} already exists upstream, and "
#                                 "`overwrite` was not set to `True`.".format(self._name))
#         unify.utils.create_evaluator(
#             self._name, self._system_message, self._class_config,
#             self._judge_models, False)
#
#     def upload_all_versions(self, overwrite=False):
#         """
#         Uploads all versions of the evaluator to the user account upstream.
#         This function will not download any versions from upstream.
#         Use `sync` to synchronize the evaluators in both directions.
#         Set `overwrite=True` to overwrite any evaluator versions with the same name
#         as those provided locally.
#
#         Args:
#             overwrite: Whether to overwrite the upstream dataset if it already exists
#         """
#         self._upload(overwrite)
#         if self._previous_version is not None:
#             self._previous_version.upload_all_versions(overwrite)
#
#     def download(self):
#         pass
#
#     def download_all_versions(self):
#         pass
#
#     def evaluate(
#             self,
#             dataset: Union[str, Dataset],
#             agent: Union[str, Agent],
#             default_prompt: Prompt = None,
#     ):
#         eval = unify.utils.trigger_evaluation(
#             dataset, agent, default_prompt, self._api_key)
#         return Evaluation(eval, api_key=self._api_key)
#
#     def __repr__(self):
#         raise NotImplemented
