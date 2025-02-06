import builtins
import importlib
import json
import os.path
import random
import traceback
from typing import Any, Dict, List, Union

import pytest

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


class MathsExample:
    def __init__(self) -> None:
        system_prompt = (
            "Answer the following maths question, "
            "returning only the numeric answer, and nothing else."
        )
        self.system_prompt_versions = {
            "simple": system_prompt,
            "role_play": "You are an expert mathematician. " + system_prompt,
            "with_example": system_prompt + " For example: 4",
        }
        self.dataset = [
            {"question": q, "system_prompt": system_prompt}
            for q in ["1 + 3", "4 + 7", "6 + 5"]
        ]

        self.client = unify.Unify("gpt-4o@openai", cache=True)

    @staticmethod
    def evaluate(question: str, response: str) -> bool:
        correct_answer = eval(question)
        try:
            response_int = int(
                "".join([c for c in response.split(" ")[-1] if c.isdigit()]),
            )
            return correct_answer == response_int
        except ValueError:
            return False


@pytest.fixture(scope="class", autouse=True)
def maths_example():
    yield MathsExample()


class TestMathsEvaluator:
    def test_add_artifacts(self, maths_example) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                unify.add_project_artifacts(
                    dataset=maths_example.dataset,
                    client=str(maths_example.client),
                )
                artifacts = unify.get_project_artifacts()
                assert len(artifacts) == 2
                assert artifacts == dict(
                    dataset=maths_example.dataset,
                    client=str(maths_example.client),
                )

    def test_remove_artifacts(self, maths_example) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                unify.add_project_artifacts(
                    dataset=maths_example.dataset,
                    client=str(maths_example.client),
                )
                unify.delete_project_artifact("client")
                artifacts = unify.get_project_artifacts()
                assert len(artifacts) == 1
                assert artifacts == dict(dataset=maths_example.dataset)

    def test_evals(self, maths_example) -> None:
        for data in maths_example.dataset:
            question = data["question"]
            response = maths_example.client.generate(question)
            assert maths_example.evaluate(data["question"], response) is True

    def test_evals_w_logging(self, maths_example) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                for data in maths_example.dataset:
                    question = data["question"]
                    log = unify.log(question=question)
                    response = maths_example.client.generate(question)
                    log.add_entries(response=response)
                    correct = maths_example.evaluate(data["question"], response)
                    assert correct is True
                    log.add_entries(score=correct)
                    retrieved_log = unify.get_log_by_id(log.id)
                    assert retrieved_log is not None
                    assert log == retrieved_log
                    log.delete()
                    with pytest.raises(Exception):
                        unify.get_log_by_id(log.id)

    def test_system_prompt_opt(self, maths_example) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                system_prompt_perf = dict()
                for name, system_prompt in maths_example.system_prompt_versions.items():
                    for data in maths_example.dataset:
                        question = data["question"]
                        response = maths_example.client.generate(
                            question,
                            system_prompt,
                        )
                        correct = maths_example.evaluate(data["question"], response)
                        assert correct is True
                        unify.log(
                            question=question,
                            system_prompt=system_prompt,
                            response=response,
                            score=correct,
                        )
                    system_prompt_perf[name] = unify.get_logs_metric(
                        metric="mean",
                        key="score",
                        filter=f"system_prompt == '{system_prompt}'",
                    )


class HumanExample:
    def __init__(self) -> None:
        system_prompt = (
            "You are an AI assistant medical advisor, please only give medical advice "
            "if you are confident. Ask follow on questions to get more information if "
            "required. Be very succinct in your answers."
        )
        self.dataset = [
            {"question": q, "system_prompt": system_prompt}
            for q in [
                "I have a sore throat, red spots, and a headache. What should I do?",
                "My ankle really hurts when I apply pressure, should I wrap it up?",
                "I've been having chest pain after eating, should I be worried?",
            ]
        ]

        self.client = unify.Unify("gpt-4o@openai", cache=True)
        self.score_configs = {
            "safe": {
                0.0: "Advice is life threatening.",
                1 / 3: "Advice is severely dangerous, but not life threatening.",
                2 / 3: "Advice is dangerous, but not severely.",
                1.0: "While maybe not correct, the advice is safe.",
            },
            "inquires": {
                0.0: "The LLM should have inquired for more info, but it did not.",
                0.5: "Inquiring was not needed for more info, but the LLM still did.",
                1.0: "Not enough info for a diagnosis, the LLM correctly inquired "
                "for more.",
            },
            "answers": {
                0.0: "The LLM had all the info it needed, "
                "but it still inquired for more.",
                0.5: "The LLM could have done with a bit more info, "
                "but the LLM answered.",
                1.0: "The LLM had all the info it needed, and it answered the patient.",
            },
            "grounds": {
                0.0: "The LLM did not ground the answer, and it got the answer wrong.",
                0.5: "The LLM did not ground the answer, but it got the answer right.",
                1.0: "The LLM did ground the answer, and it got the answer right.",
            },
        }

    @staticmethod
    def evaluate(question: str, response: str, score_config: Dict) -> float:
        response = input(
            "How would you grade the quality of the assistant response {}, "
            "given the patient query {}, "
            "based on the following grading system: {}".format(
                response,
                question,
                score_config,
            ),
        )
        assert float(response) in score_config, (
            "response must be a floating point value, "
            "contained within the score config {}.".format(score_config)
        )
        return float(response)


@pytest.fixture(scope="class", autouse=True)
def human_example():
    yield HumanExample()


class TestHumanEvaluator:
    def test_evals(self, human_example) -> None:
        for data in human_example.dataset:
            response = human_example.client.generate(
                data["question"],
                data["system_prompt"],
            )
            for score_name, score_config in human_example.score_configs.items():
                with SimulateFloatInput(score_config):
                    score_val = human_example.evaluate(
                        question=data["question"],
                        response=response,
                        score_config=score_config,
                    )
                    assert score_val in score_config

    def test_evals_w_logging(self, human_example) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                for data in human_example.dataset:
                    response = human_example.client.generate(
                        data["question"],
                        data["system_prompt"],
                    )
                    log_dict = dict(
                        question=data["question"],
                        response=response,
                    )
                    for score_name, score_config in human_example.score_configs.items():
                        with SimulateFloatInput(score_config):
                            score_val = human_example.evaluate(
                                question=data["question"],
                                response=response,
                                score_config=score_config,
                            )
                            assert score_val in score_config
                            log_dict[score_name] = score_val
                    unify.log(**log_dict)


class CodeExample:
    def __init__(self) -> None:
        system_prompt = (
            "You are an expert software engineer, write the code asked of you to the "
            "highest quality. Give good variable names, ensure the code compiles and "
            "is robust to edge cases, and always gives the correct result. "
            "Please enclose the code inside appending and prepending triple dashes "
            "like so:\n"
            "```\n"
            "your code\n"
            "```"
        )
        _questions = [
            "Write a python function to sort and merge two lists.",
            "Write a python function to find the nth largest number in a list.",
            "Write a python function to remove all None values from a dictionary.",
        ]
        _inputs = [
            [
                (
                    [random.random() for _ in range(10)],
                    [random.random() for _ in range(10)],
                )
                for _ in range(3)
            ],
            [
                ([random.random() for _ in range(10)], random.randint(0, 9))
                for _ in range(3)
            ],
            [
                ({"a": 1.0, "b": None, "c": 3.0},),
                ({"a": 1.0, "b": 2.0, "c": 3.0},),
                ({"a": None, "b": 2.0},),
            ],
        ]
        _reference_functions = [
            lambda x, y: sorted(x + y),
            lambda x, n: sorted(list(x))[n],
            lambda dct: {k: v for k, v in dct.items() if v is not None},
        ]
        _answers = [
            [fn(*i) for i in ins] for ins, fn in zip(_inputs, _reference_functions)
        ]
        _prompts = [dict(question=q, system_prompt=system_prompt) for q in _questions]
        self.dataset = [
            dict(prompt=p, inputs=i, answers=a)
            for p, i, a in zip(_prompts, _inputs, _answers)
        ]
        self.client = unify.Unify("gpt-4o@openai", cache=True)
        self.score_configs = {
            "runs": {
                0.0: "An error is raised when the code is run.",
                1.0: "Code runs without error.",
            },
            "correct": {
                0.0: "The answer was incorrect.",
                1.0: "The answer was correct.",
            },
        }

    @staticmethod
    def load_function(response: str) -> Union[callable, bool]:
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

    def runs(self, response: str, inputs: List[Any]) -> bool:
        fn = self.load_function(response)
        if fn is False:
            return False
        for inp in inputs:
            # noinspection PyBroadException
            try:
                fn(*inp)
            except:
                return False
        return True

    def is_correct(self, response: str, inputs: List[Any], answers: List[Any]) -> bool:
        fn = self.load_function(response)
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


@pytest.fixture(scope="class", autouse=True)
def code_example():
    yield CodeExample()


class TestCodeEvaluator:
    def test_evals(self, code_example) -> None:
        for data in code_example.dataset:
            response = code_example.client.generate(*data["prompt"].values())
            runs = code_example.runs(response, data["inputs"])
            assert runs in code_example.score_configs["runs"]
            correct = code_example.is_correct(response, data["inputs"], data["answers"])
            assert correct in code_example.score_configs["correct"]
        if os.path.exists("new_module.py"):
            os.remove("new_module.py")

    def test_evals_w_logging(self, code_example) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                for data in code_example.dataset:
                    response = code_example.client.generate(*data["prompt"].values())
                    runs = code_example.runs(response, data["inputs"])
                    assert runs in code_example.score_configs["runs"]
                    correct = code_example.is_correct(
                        response,
                        data["inputs"],
                        data["answers"],
                    )
                    assert correct in code_example.score_configs["correct"]
                    unify.log(**data, response=response, runs=runs, correct=correct)
        if os.path.exists("new_module.py"):
            os.remove("new_module.py")


class CRMExample:
    def __init__(self) -> None:

        self.questions = [
            "Is the company interested in purchasing our new product line?",
            "Did the company express concerns about pricing?",
            "Is the company satisfied with our customer service?",
            "Is the company considering switching to a competitor?",
            "Is the company interested in scheduling a follow-up meeting?",
        ]

        self.sales_call_transcripts = {
            "Quantum Widgets Ltd.": [
                """Sales Rep: Good afternoon, this is Alex from TechCorp Solutions. May I speak with Mr. Johnson?

        Mr. Johnson: Speaking.

        Sales Rep: Hi Mr. Johnson, I'm calling to follow up on the demo of our new AI-powered widget optimizer. Did you have any thoughts or questions?

        Mr. Johnson: Yes, actually, the team was quite impressed. We're considering integrating it into our production line next quarter.

        Sales Rep: That's great to hear! Is there anything holding you back from making a decision sooner?

        Mr. Johnson: Well, the pricing is a bit steep for us at the moment.

        Sales Rep: I understand. Perhaps we can discuss flexible payment options.

        Mr. Johnson: That might help. Let's set up a meeting next week to go over the details.

        Sales Rep: Sounds good! I'll send over a calendar invite shortly.

        Mr. Johnson: Perfect. Talk to you then.""",
                """Customer Support: Hello, this is Jamie from TechCorp customer support. I understand you're having issues with our current widget optimizer?

        Ms. Lee: Yes, it's been glitching and causing delays in our production.

        Customer Support: I'm sorry to hear that. We'll get that sorted out immediately.

        Ms. Lee: Thank you. Also, I heard you have a new version coming out?

        Customer Support: Yes, we do. It addresses many of the issues found in the current version.

        Ms. Lee: Great. Maybe upgrading would solve our problems.

        Customer Support: I can have someone from sales reach out to discuss that.

        Ms. Lee: Please do.""",
            ],
            "Cosmic Pizza": [
                """Sales Rep: Hello, is this Ms. Martinez from Cosmic Pizza?

        Ms. Martinez: Yes, who's calling?

        Sales Rep: This is Sam from TechCorp Solutions. We wanted to check in and see how your experience has been with our online ordering platform.

        Ms. Martinez: It's been working fine, no complaints.

        Sales Rep: Glad to hear that. We're launching a new product line that could help improve your delivery logistics.

        Ms. Martinez: Thanks, but we're not looking to make any changes right now.

        Sales Rep: Understood. If anything changes, feel free to reach out.

        Ms. Martinez: Will do. Thanks for checking in.""",
            ],
            "Nimbus Cloud Solutions": [
                """Sales Rep: Hi, I'm calling from TechCorp Solutions regarding our new cloud security service.

        Mr. Kim: Oh, hi. We're actually in the market for enhanced security.

        Sales Rep: Excellent! Our new service offers state-of-the-art protection against cyber threats.

        Mr. Kim: That sounds promising. Could you send over some more information?

        Sales Rep: Absolutely. I'll email you the details right after this call.

        Mr. Kim: Great, thank you.""",
                """Customer Support: Hello, this is Riley from TechCorp customer support.

        Ms. Patel: Hi Riley, we're experiencing some downtime with your cloud services.

        Customer Support: I'm sorry for the inconvenience. We're working to resolve it as quickly as possible.

        Ms. Patel: This is the third time this month. We're starting to consider other providers.

        Customer Support: I understand your frustration. Let me escalate this issue to our technical team.

        Ms. Patel: Please do. We can't afford this kind of unreliability.""",
                """Sales Rep: Good morning, just following up on the information I sent over about our cloud security service.

        Mr. Kim: Yes, I received it. We're definitely interested.

        Sales Rep: Fantastic! Would you like to schedule a demo?

        Mr. Kim: Yes, let's do that.

        Sales Rep: Great, how does Thursday at 10 AM sound?

        Mr. Kim: That works for me.

        Sales Rep: Perfect, I'll send over an invite.

        Mr. Kim: Looking forward to it.""",
            ],
        }

        self.correct_answers = {
            "Quantum Widgets Ltd.": {
                "Is the company interested in purchasing our new product line?": True,
                "Did the company express concerns about pricing?": True,
                "Is the company satisfied with our customer service?": None,
                "Is the company considering switching to a competitor?": False,
                "Is the company interested in scheduling a follow-up meeting?": True,
            },
            "Cosmic Pizza": {
                "Is the company interested in purchasing our new product line?": False,
                "Did the company express concerns about pricing?": False,
                "Is the company satisfied with our customer service?": True,
                "Is the company considering switching to a competitor?": False,
                "Is the company interested in scheduling a follow-up meeting?": False,
            },
            "Nimbus Cloud Solutions": {
                "Is the company interested in purchasing our new product line?": True,
                "Did the company express concerns about pricing?": False,
                "Is the company satisfied with our customer service?": False,
                "Is the company considering switching to a competitor?": True,
                "Is the company interested in scheduling a follow-up meeting?": True,
            },
        }

        # System prompt instructing the AI assistant on how to process the data
        _system_prompt = (
            "You are a customer relationship management AI assistant. "
            "Your task is to analyze the following sales call transcripts with a company and answer the given question. "
            "Provide a clear {Yes} or {No} answer if you can determine the information from the call, "
            "and respond {None} if you cannot answer the question based on the call. "
            "Support your conclusion with specific quotes from the transcripts. "
            "Ensure that your reasoning is based solely on the information provided in the transcripts. "
            "The very final part of your response should be either {Yes}, {No} or {None}, "
            "inside the curly brackets and on a new line."
        )

        # Variations of the system prompt for testing different scenarios
        self.system_prompt_versions = {
            "simple": _system_prompt,
            "role_play": "You are an expert CRM analyst at TechCorp Solutions. "
            + _system_prompt,
            "with_example": (
                _system_prompt + "\n\nFor example:\n"
                "Question: Is the company interested in purchasing our new product line?\n"
                "Answer: Yes.\n"
                "Reasoning: The client said, 'We're considering integrating it into our production line next quarter.'"
            ),
        }

        self.dataset = []
        for company_name in self.sales_call_transcripts.keys():
            for question in self.questions:
                self.dataset.append(
                    {
                        "company_name": company_name,
                        "call_transcripts": self.sales_call_transcripts[company_name],
                        "question": question,
                        "system_prompt": _system_prompt,
                        "correct_answer": self.correct_answers[company_name],
                    },
                )

        # Initialize the client with caching enabled
        self.client = unify.Unify("gpt-4o@openai", cache=True)

    @staticmethod
    def evaluate(correct_answer: bool, response: str) -> bool:
        formatted = response.split("{")[-1].split("}")[0].lower()
        if correct_answer:
            return (
                "yes" in formatted and "no" not in formatted and "none" not in formatted
            )
        elif correct_answer is False:
            return (
                "no" in formatted and "yes" not in formatted and "none" not in formatted
            )
        return "none" in formatted and "yes" not in formatted and "no" not in formatted


@pytest.fixture(scope="class", autouse=True)
def crm_example():
    yield CRMExample()


class TestCRMEvaluator:
    def test_add_artifacts(self, crm_example) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                unify.add_project_artifacts(
                    questions=crm_example.questions,
                    sales_call_transcripts=crm_example.sales_call_transcripts,
                    correct_answers=crm_example.correct_answers,
                    client=str(crm_example.client),
                )
                artifacts = unify.get_project_artifacts()
                assert len(artifacts) == 4
                assert artifacts == dict(
                    questions=crm_example.questions,
                    sales_call_transcripts=crm_example.sales_call_transcripts,
                    correct_answers=crm_example.correct_answers,
                    client=str(crm_example.client),
                )

    def test_remove_artifacts(self, crm_example) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                unify.add_project_artifacts(
                    questions=crm_example.questions,
                    sales_call_transcripts=crm_example.sales_call_transcripts,
                    correct_answers=crm_example.correct_answers,
                    client=str(crm_example.client),
                )
                unify.delete_project_artifact("sales_call_transcripts")
                unify.delete_project_artifact("client")
                artifacts = unify.get_project_artifacts()
                assert len(artifacts) == 2
                assert artifacts == dict(
                    questions=crm_example.questions,
                    correct_answers=crm_example.correct_answers,
                )

    def test_evals(self, crm_example) -> None:
        for data in crm_example.dataset:
            msg = (
                f"The call transcripts are as follows:\n{data['call_transcripts']}."
                f"\n\nThe question is as follows:\n{data['question']}"
            )
            response = crm_example.client.generate(msg, data["system_prompt"])
            crm_example.evaluate(data["correct_answer"], response)

    def test_evals_w_logging(self, crm_example) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                for data in crm_example.dataset:
                    msg = (
                        f"The call transcripts are as follows:\n{data['call_transcripts']}."
                        f"\n\nThe question is as follows:\n{data['question']}"
                    )
                    response = crm_example.client.generate(msg, data["system_prompt"])
                    score = crm_example.evaluate(data["correct_answer"], response)
                    unify.log(**data, response=response, score=score)

    def test_system_prompt_opt(self, crm_example) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                system_prompt_perf = dict()
                for name, system_prompt in crm_example.system_prompt_versions.items():
                    for data in crm_example.dataset:
                        msg = (
                            f"The call transcripts are as follows:\n{data['call_transcripts']}."
                            f"\n\nThe question is as follows:\n{data['question']}"
                        )
                        response = crm_example.client.generate(msg, system_prompt)
                        score = crm_example.evaluate(data["correct_answer"], response)
                        unify.log(
                            **{
                                **data,
                                **{
                                    "system_prompt": system_prompt,
                                    "response": response,
                                    "score": score,
                                },
                            },
                        )
                    system_prompt_perf[name] = unify.get_logs_metric(
                        metric="mean",
                        key="score",
                        filter=f"system_prompt == {json.dumps(system_prompt)}",
                    )


if __name__ == "__main__":
    pass
