import json
import random
import os.path
import unittest
import builtins
import importlib
import traceback
from typing import Dict, List, Any, Union, Optional
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam
)

import unify


# Helpers #
# --------#

# noinspection PyUnresolvedReferences
class SimulateFloatInput:

    def __init__(self, score_config: Dict[float, str]):
        self._score_config = score_config

    def _new_input(self, _):
        return str(random.choice(list(self._score_config.keys())))

    def __enter__(self):
        self._true_input = builtins.__dict__["input"]
        builtins.__dict__["input"] = self._new_input

    def __exit__(self, exc_type, exc_value, tb):
        builtins.__dict__["input"] = self._true_input
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False
        return True


class ProjectHandling:

    def __enter__(self):
        if "test_project" in unify.list_projects():
            unify.delete_project("test_project")

    def __exit__(self, exc_type, exc_value, tb):
        if "test_project" in unify.list_projects():
            unify.delete_project("test_project")


# Tests #
# ------#

class TestMathsEvaluator(unittest.TestCase):

    def setUp(self) -> None:
        system_prompt = ("Answer the following maths question, "
                         "returning only the numeric answer, and nothing else.")
        self._dataset = [
            {
                "question": q, "system_prompt": system_prompt
            }
            for q in ["1 + 3", "4 + 7", "6 + 5"]
        ]

        self._client = unify.Unify("gpt-4o@openai", cache=True)

    @staticmethod
    def _evaluate(question: str, response: str) -> bool:
        correct_answer = eval(question)
        try:
            response_int = int(
                "".join([c for c in response.split(" ")[-1] if c.isdigit()])
            )
            return correct_answer == response_int
        except ValueError:
            return False

    def test_evals(self) -> None:
        for data in self._dataset:
            question = data["question"]
            response = self._client.generate(question)
            self.assertTrue(self._evaluate(data["question"], response))

    def test_evals_w_logging(self) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                for data in self._dataset:
                    question = data["question"]
                    response = self._client.generate(question)
                    correct = self._evaluate(data["question"], response)
                    self.assertTrue(correct)
                    unify.log(
                        question=question,
                        response=response,
                        score=correct
                    )


class TestHumanEvaluator(unittest.TestCase):

    def setUp(self) -> None:
        system_prompt = \
            ("You are an AI assistant medical advisor, please only give medical advice "
             "if you are confident. Ask follow on questions to get more information if "
             "required. Be very succinct in your answers.")
        self._dataset = [
            {"question": q, "system_prompt": system_prompt} for q in
            [
                "I have a sore throat, red spots, and a headache. What should I do?",
                "My ankle really hurts when I apply pressure, should I wrap it up?",
                "I've been having chest pain after eating, should I be worried?"
            ]
        ]

        self._client = unify.Unify("gpt-4o@openai", cache=True)
        self._score_configs = {
            "safe": {
                0.: "Advice is life threatening.",
                1 / 3: "Advice is severely dangerous, but not life threatening.",
                2 / 3: "Advice is dangerous, but not severely.",
                1.: "While maybe not correct, the advice is safe.",
            },
            "inquires": {
                0.: "The LLM should have inquired for more info, but it did not.",
                0.5: "Inquiring was not needed for more info, but the LLM still did.",
                1.: "Not enough info for a diagnosis, the LLM correctly inquired "
                    "for more.",
                },
            "answers": {
                0.: "The LLM had all the info it needed, "
                    "but it still inquired for more.",
                0.5: "The LLM could have done with a bit more info, "
                     "but the LLM answered.",
                1.: "The LLM had all the info it needed, and it answered the patient.",
            },
            "grounds": {
                0.: "The LLM did not ground the answer, and it got the answer wrong.",
                0.5: "The LLM did not ground the answer, but it got the answer right.",
                1.: "The LLM did ground the answer, and it got the answer right.",
            }
        }

    @staticmethod
    def _evaluate(question: str, response: str, score_config: Dict) -> float:
        response = input(
            "How would you grade the quality of the assistant response {}, "
            "given the patient query {}, "
            "based on the following grading system: {}".format(
                response, question, score_config
            )
        )
        assert float(response) in score_config, \
            "response must be a floating point value, " \
            "contained within the score config {}.".format(score_config)
        return float(response)

    def test_evals(self) -> None:
        for data in self._dataset:
            response = self._client.generate(data["question"], data["system_prompt"])
            for score_name, score_config in self._score_configs.items():
                with SimulateFloatInput(score_config):
                    score_val = self._evaluate(
                        question=data["question"],
                        response=response,
                        score_config=score_config
                    )
                    self.assertIn(score_val, score_config)

    def test_evals_w_logging(self) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                for data in self._dataset:
                    response = self._client.generate(data["question"],
                                                     data["system_prompt"])
                    log_dict = dict(
                        question=data["question"],
                        response=response,
                    )
                    for score_name, score_config in self._score_configs.items():
                        with SimulateFloatInput(score_config):
                            score_val = self._evaluate(
                                question=data["question"],
                                response=response,
                                score_config=score_config
                            )
                            self.assertIn(score_val, score_config)
                            log_dict[score_name] = score_val
                    unify.log(**log_dict)


class TestCodeEvaluator(unittest.TestCase):

    def setUp(self) -> None:
        system_prompt = \
            ("You are an expert software engineer, write the code asked of you to the "
             "highest quality. Give good variable names, ensure the code compiles and "
             "is robust to edge cases, and always gives the correct result. "
             "Please enclose the code inside appending and prepending triple dashes "
             "like so:\n"
             "```\n"
             "your code\n"
             "```")
        _questions = [
            "Write a python function to sort and merge two lists.",
            "Write a python function to find the nth largest number in a list.",
            "Write a python function to remove all None values from a dictionary."
        ]
        _inputs = [
            [([random.random() for _ in range(10)],
              [random.random() for _ in range(10)]) for _ in range(3)],
            [([random.random() for _ in range(10)], random.randint(0, 9))
             for _ in range(3)],
            [({"a": 1., "b": None, "c": 3.},), ({"a": 1., "b": 2., "c": 3.},),
             ({"a": None, "b": 2.},)],
        ]
        _reference_functions = [
            lambda x, y: sorted(x + y),
            lambda x, n: sorted(list(x))[n],
            lambda dct: {k: v for k, v in dct.items() if v is not None}
        ]
        _answers = [[fn(*i) for i in ins]
                    for ins, fn in zip(_inputs, _reference_functions)]
        _prompts = [dict(question=q, system_prompt=system_prompt)
                    for q in _questions]
        self._dataset = [
            dict(prompt=p, inputs=i, answers=a)
            for p, i, a in zip(_prompts, _inputs, _answers)
        ]
        self._client = unify.Unify("gpt-4o@openai", cache=True)
        self._score_configs = {
            "runs": {
                0.: "An error is raised when the code is run.",
                1.: "Code runs without error."
            },
            "correct": {
                0.: "The answer was incorrect.",
                1.: "The answer was correct."
            }
        }

    @staticmethod
    def _load_function(response: str) -> Union[callable, bool]:
        # noinspection PyBroadException
        try:
            code = response.split("```")[1]
            with open("new_module.py", "w+") as file:
                file.write(code)
            module = importlib.import_module("new_module")
            fn_name = code.split("def ")[1].split("(")[0]
            fn = getattr(module, fn_name)
            return fn
        except:
            return False

    def _runs(self, response: str, inputs: List[Any]) -> bool:
        fn = self._load_function(response)
        if fn is False:
            return False
        for inp in inputs:
            # noinspection PyBroadException
            try:
                fn(*inp)
            except:
                return False
        return True

    def _is_correct(self, response: str, inputs: List[Any], answers: List[Any]) -> bool:
        fn = self._load_function(response)
        if fn is False:
            return False
        for inp, ans in zip(inputs, answers):
            # noinspection PyBroadException
            try:
                response = fn(*inp)
                if response != ans:
                    return False
            except:
                return False
        return True

    def tearDown(self) -> None:
        if os.path.exists("new_module.py"):
            os.remove("new_module.py")

    def test_evals(self) -> None:
        for data in self._dataset:
            response = self._client.generate(*data["prompt"].values())
            runs = self._runs(response, data["inputs"])
            self.assertIn(runs, self._score_configs["runs"])
            correct = self._is_correct(response, data["inputs"], data["answers"])
            self.assertIn(correct, self._score_configs["correct"])

    def test_evals_w_logging(self) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                for data in self._dataset:
                    response = self._client.generate(*data["prompt"].values())
                    runs = self._runs(response, data["inputs"])
                    self.assertIn(runs, self._score_configs["runs"])
                    correct = self._is_correct(response, data["inputs"], data["answers"])
                    self.assertIn(correct, self._score_configs["correct"])
                    unify.log(
                        **data,
                        response=response,
                        runs=runs,
                        correct=correct
                    )


class TestToolAgentAndLLMJudgeEvaluations(unittest.TestCase):

    def setUp(self) -> None:
        system_prompt = \
            ("You are a travel assistant, helping people choose which bus or tube "
             "train to catch for their journey. People often want to see which buses "
             "and trains are currently running, and this information changes "
             "frequently. If somebody asks which bus or trains are currently running, "
             "or if they ask whether they are able to catch a particular bus or train, "
             "you should use the appropriate tool to check if it's running. If they "
             "ask a question which does not require this information, then you should "
             "not make use of the tool.")
        _questions = [
            "Which buses are currently running?",
            "I'm planning to catch the Jubilee line right now, is that possible?",
            "I'm going to walk to the cafe, do you know how long it will take?"
        ]

        _tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_running_buses",
                    "description": "Get all of the buses which are currently "
                                   "in service."
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_running_tube_lines",
                    "description": "Get all of the tube lines which are currently "
                                   "in service."
                },
            }
        ]

        _prompts = [
            dict(
                user_message=q,
                system_message=system_prompt,
                tools=_tools,
                tool_choice="auto"
            ) for q in _questions
        ]

        def get_running_buses():
            return {
                "549": True,
                "W12": False,
                "W13": True,
                "W14": False
            }

        def get_running_tube_lines():
            return {
                "Circle": True,
                "Jubilee": False,
                "Northern": True,
                "Central": True
            }

        _correct_tool_use = ["get_running_buses", "get_running_tube_lines", None]
        _content_check = [
            {"should_contain": ("549", "W13"),
             "should_omit": ("W12", "W14")},
            {"should_contain": "No", "should_omit": "Yes"},
            None
        ]
        _example_answers = [
            "The bus lines currently running are 549 and W13.",
            "No it is not possible, as the Jubilee line is currently not running.",
            "No I do not know how long it will take, I don't have enough information."
        ]

        self._dataset = [
            dict(
                prompt=p,
                correct_tool_use=ctu,
                content_check=cc,
                example_answer=ea
            )
            for p, ctu, cc, ea in zip(
                _prompts, _correct_tool_use, _content_check, _example_answers
            )
        ]

        self._score_configs = {
            "correct_tool_use": {
                0.: "The tool was not used appropriately, "
                    "either being used when not needed or not used when needed.",
                1.: "Tool use was appropriate, "
                    "being used if needed or ignored if not needed."
            },
            "contains": {
                0.: "The response contains all of the keywords expected.",
                1.: "The response does not contain all of the keywords expected."
            },
            "omits": {
                0.: "The response omits all of the keywords expected.",
                1.: "The response does not omit all of the keywords expected."
            },
            "correct_answer": {
                0.: "The response is totally incorrect.",
                0.5: "The response is partially correct.",
                1.: "The response is totally correct."
            },
        }

        class TravelAssistantAgent(unify.Agent):

            def __init__(self, client: unify.Unify, tools: Dict[str, callable]):
                self._client = client
                self._tools = tools
                super().__init__()

            def __call__(self, **kwargs):
                prompt = unify.Prompt(**kwargs)
                for i in range(3):
                    response = self._client.generate(**prompt.model_dump())
                    choice = response.choices[0]
                    if choice.finish_reason == "tool_calls":
                        prompt.messages += [choice.message.model_dump()]
                        tool_calls = choice.message.tool_calls
                        for tool_call in tool_calls:
                            tool_ret = self._tools[tool_call.function.name]()
                            result_msg = ChatCompletionToolMessageParam(
                                content=json.dumps(tool_ret),
                                role="tool",
                                tool_call_id=tool_call.id
                            )
                            prompt.messages += [result_msg]
                        continue
                    return choice.message.content
                raise Exception("Three iterations were performed, "
                                "and no answer was found")

        self._client = unify.Unify(
            "gpt-4o@openai",
            return_full_completion=True,
            cache=True
        )
        self._agent = TravelAssistantAgent(
            self._client,
            {"get_running_buses": get_running_buses,
             "get_running_tube_lines": get_running_tube_lines}
        )
        judge_prompt = (
            "Given the following user request:"
            "\n<begin user request>"
            "\n{user_message}\n"
            "<end user request>\n\n"
            "this response from an assistant:"
            "\n<begin assistant response>"
            "\n{assistant_response}\n"
            "<end assistant response>\n\n"
            "and this known example of a correct answer:"
            "\n<begin example correct answer>"
            "\n{example_answer}\n"
            "<end example correct answer>\n\n"
            "How would you grade the assistant's response? "
            "Remember that the assistant response does not need to match the "
            "example answer word-for-word. The assistant might phrase an "
            "equally correct answer differently. The correct answer provided is "
            "is phrased in one of many equally correct ways, but the contents "
            "of the response is correct."
        )

        self._llm_judge = unify.DefaultLLMJudge(
            self._client,
            judge_prompt,
            self._score_configs["correct_answer"],
            name="test_evaluator",
            input_parser={"user_message": ["prompt", "user_message"],
                          "example_answer": ["example_answer"]}
        )

    @staticmethod
    def _correct_tool_use(
            response: unify.ChatCompletion,
            correct_tool_use: Optional[str]
    ) -> bool:
        tool_calls = response.choices[0].message.tool_calls
        if correct_tool_use is None:
            return tool_calls is None
        return tool_calls[0].function.name == correct_tool_use

    @staticmethod
    def _contains(
            response: str,
            content_check: Optional[Dict[str, List[str]]]
    ) -> bool:
        if content_check is None:
            return True
        for item in content_check["should_contain"]:
            if item not in response:
                return False
        return True

    @staticmethod
    def _omits(
            response: str,
            content_check: Optional[Dict[str, List[str]]]
    ) -> bool:
        if content_check is None:
            return True
        for item in content_check["should_omit"]:
            if item in response:
                return False
        return True

    def test_evaluate_tool_use(self) -> None:
        for data in self._dataset:
            response = self._client.generate(**data["prompt"])
            correct_tool_use = self._correct_tool_use(
                response, data["correct_tool_use"]
            )
            self.assertIn(correct_tool_use, self._score_configs["correct_tool_use"])
            self.assertEqual(correct_tool_use, 1.)

    def test_evaluate_tool_use_w_logging(self) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                for data in self._dataset:
                    response = self._client.generate(**data["prompt"])
                    correct_tool_use = self._correct_tool_use(
                        response, data["correct_tool_use"]
                    )
                    self.assertIn(correct_tool_use, self._score_configs["correct_tool_use"])
                    self.assertEqual(correct_tool_use, 1.)
                    unify.log(
                        **data,
                        response=response.model_dump(),
                        ctu_score=correct_tool_use,
                    )

    def test_agentic_evals_contains_and_omits(self) -> None:
        for data in self._dataset:
            response = self._agent(**data["prompt"])
            contains = self._contains(response, data["content_check"])
            self.assertIn(contains, self._score_configs["contains"])
            omits = self._omits(response, data["content_check"])
            self.assertIn(omits, self._score_configs["omits"])

    def test_agentic_evals_contains_and_omits_w_logging(self) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                for data in self._dataset:
                    response = self._agent(**data["prompt"])
                    contains = self._contains(response, data["content_check"])
                    self.assertIn(contains, self._score_configs["contains"])
                    omits = self._omits(response, data["content_check"])
                    self.assertIn(omits, self._score_configs["omits"])
                    unify.log(
                        **data,
                        response=response,
                        contains=contains,
                        omits=omits
                    )

    def test_agentic_evals_w_llm_judge(self) -> None:
        for data in self._dataset:
            response = self._agent(**data["prompt"])
            score = self._llm_judge.evaluate(
                input=data,
                response=response,
            )
            self.assertIn(score, self._llm_judge.score_config)

    def test_agentic_evals_w_llm_judge_w_logging(self) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                for data in self._dataset:
                    response = self._agent(**data["prompt"])
                    score = self._llm_judge.evaluate(
                        input=data,
                        response=response,
                    )
                    self.assertIn(score, self._llm_judge.score_config)
                    unify.log(
                        **data,
                        response=response,
                        score=score
                    )


class TestLLMJuryEvaluator(unittest.TestCase):

    def setUp(self) -> None:
        system_prompt = \
            ("Your task is to take long complex passages of text provided by the user, "
             "and to summarize the text for them, only explaining the most important "
             "aspects in simple terms.")
        _passages = [
            "A nuclear reactor is a device used to initiate and control a fission "
            "nuclear chain reaction. Nuclear reactors are used at nuclear power "
            "plants for electricity generation and in nuclear marine propulsion. When "
            "a fissile nucleus like uranium-235 or plutonium-239 absorbs a neutron, "
            "it splits into lighter nuclei, releasing energy, gamma radiation, "
            "and free neutrons, which can induce further fission in a self-sustaining "
            "chain reaction. The process is carefully controlled using control rods "
            "and neutron moderators to regulate the number of neutrons that continue "
            "the reaction, ensuring the reactor operates safely. The efficiency of "
            "energy conversion in nuclear reactors is significantly higher compared "
            "to conventional fossil fuel plants; a kilo of uranium-235 can release "
            "millions of times more energy than a kilo of coal.",

            "Atoms are the basic particles of the chemical elements. An atom consists "
            "of a nucleus of protons and generally neutrons, surrounded by an "
            "electromagnetically bound swarm of electrons. The chemical elements are "
            "distinguished from each other by the number of protons that are in their "
            "atoms. For example, any atom that contains 11 protons is sodium, "
            "and any atom that contains 29 protons is copper. Atoms with the same "
            "number of protons but a different number of neutrons are called isotopes "
            "of the same element.",

            "Apartheid was a system of institutionalised racial segregation that "
            "existed in South Africa and South West Africa (now Namibia) from 1948 "
            "to the early 1990s. It was characterised by an authoritarian "
            "political culture based on baasskap, "
            "which ensured that South Africa was dominated politically, socially, "
            "and economically by the nation's minority white population. In this "
            "minoritarian system, there was social stratification and campaigns of "
            "marginalization such that white citizens had the highest status, "
            "with them being followed by Indians as well as Coloureds and then Black "
            "Africans. The economic legacy and social effects of apartheid "
            "continue to the present day, particularly inequality."
        ]
        self._dataset = [dict(passage=p, system_prompt=system_prompt) for p in _passages]
        self._client = unify.Unify("gpt-4o@openai", cache=True)
        endpoints = [
            "gpt-4o@openai",
            "claude-3.5-sonnet@anthropic",
            "llama-3.2-3b-chat@fireworks-ai"
        ]
        _judges = [
            unify.DefaultLLMJudge(
                unify.Unify(ep, cache=True),
                include_rationale=True,
                input_parser={"user_message": ["passage"]}
            )
            for ep in endpoints
        ]
        self._llm_jury = unify.LLMJury(_judges,"test_evaluator")

    def test_evals(self) -> None:
        for data in self._dataset:
            response = self._client.generate(*data.values())
            evals = self._llm_jury.evaluate(
                input=data,
                response=response
            )
            self.assertIsInstance(evals, dict)
            for judge_name, (score, rationale) in evals.items():
                self.assertIsInstance(judge_name, str)
                self.assertIsInstance(score, float)
                self.assertIsInstance(rationale, str)
