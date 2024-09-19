"""Unify python module."""
import os

if "UNIFY_BASE_URL" in os.environ.keys():
    BASE_URL = os.environ["UNIFY_BASE_URL"]
else:
    BASE_URL = "https://api.unify.ai/v0"

from .utils import (
    credits,
    custom_api_keys,
    custom_endpoints,
    datasets,
    efficiency_benchmarks,
    evaluations,
    evaluators,
    helpers,
    logging,
    router_configurations,
    router_deployment,
    router_training,
    supported_endpoints,
)
from .utils.credits import *
from .utils.custom_api_keys import *
from .utils.custom_endpoints import *
from .utils.datasets import *
from .utils.efficiency_benchmarks import *
from .utils.evaluations import *
from .utils.evaluators import *
from .utils.helpers import *
from .utils.logging import *
from .utils.router_configurations import *
from .utils.router_deployment import *
from .utils.router_training import *
from .utils.supported_endpoints import *

from .chat import chatbot, clients
from .chat.clients import multi_llm
from .chat.chatbot import *
from unify.chat.clients.uni_llm import *
from unify.chat.clients.multi_llm import *

from .agent import *
from .casting import *
from .dataset import *
from .evaluation import *
from .evaluator import *
from .logging import *
from .repr import *
from .types import *
