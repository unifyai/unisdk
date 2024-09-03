import unittest
import requests
from unify.utils import (
    create_evaluator,
    rename_evaluator,
    get_evaluator,
    delete_evaluator,
    list_evaluators,
)


class TestCreateEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator_config = {
            "name": "test_evaluator",
            "judge_models": "claude-3.5-sonnet@aws-bedrock",
            "client_side": False,
        }

    def test_create_evaluator(self):
        result = create_evaluator(self.evaluator_config)
        self.assertIsInstance(result, dict)
        self.assertIn("info", result)
        self.assertEqual(result["info"], "Evaluator created successfully!")

    def tearDown(self):
        try:
            delete_evaluator(self.evaluator_config["name"])
        except:
            pass


class TestGetEvaluator(unittest.TestCase):
    def setUp(self):
        self.test_evaluator_name = "test_evaluator"
        self.test_evaluator_config = {
            "name": self.test_evaluator_name,
            "judge_models": "claude-3.5-sonnet@aws-bedrock",
        }
        create_evaluator(self.test_evaluator_config)

    def tearDown(self):
        try:
            delete_evaluator(self.test_evaluator_name)
        except:
            pass

    def test_get_evaluator(self):
        result = get_evaluator(self.test_evaluator_name)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], self.test_evaluator_name)
        self.assertEqual(
            result["judge_models"], self.test_evaluator_config["judge_models"]
        )

    def test_get_invalid_evaluator(self):
        with self.assertRaises(requests.HTTPError):
            get_evaluator("non_existent_evaluator")


class TestDeleteEvaluator(unittest.TestCase):
    def setUp(self):
        self.test_evaluator_name = "test_evaluator_for_deletion"
        self.test_evaluator_config = {
            "name": self.test_evaluator_name,
            "judge_models": "claude-3.5-sonnet@aws-bedrock",
        }
        create_evaluator(self.test_evaluator_config)

    def test_delete_evaluator(self):
        initial_evaluators = list_evaluators()
        self.assertIn(
            self.test_evaluator_name,
            initial_evaluators,
            "Test evaluator not found in initial list",
        )

        response = delete_evaluator(self.test_evaluator_name)
        self.assertIsInstance(response, dict, "Response is not a dictionary")
        self.assertIn("info", response, "Response does not contain an 'info' key")
        self.assertEqual(
            response["info"],
            "Evaluator deleted successfully!",
            "Unexpected response message",
        )

        updated_evaluators = list_evaluators()
        self.assertNotIn(
            self.test_evaluator_name,
            updated_evaluators,
            "Test evaluator still present after deletion",
        )

        with self.assertRaises(Exception):
            get_evaluator(self.test_evaluator_name)

    def tearDown(self):
        try:
            delete_evaluator(self.test_evaluator_name)
        except:
            pass


class TestRenameEvaluator(unittest.TestCase):
    def setUp(self):
        self.original_name = "test_original_name_evaluator"
        self.new_name = "renamed_evaluator"
        self.evaluator_config = {
            "name": self.original_name,
            "judge_models": "claude-3.5-sonnet@aws-bedrock",
        }
        create_evaluator(self.evaluator_config)

    def test_rename_evaluator(self):
        result = rename_evaluator(self.original_name, self.new_name)
        self.assertIsInstance(result, dict)
        self.assertIn("info", result)
        self.assertEqual(result["info"], "Evaluator renamed successfully!")

        with self.assertRaises(requests.HTTPError):
            get_evaluator(self.original_name)

        renamed_evaluator = get_evaluator(self.new_name)
        self.assertEqual(renamed_evaluator["name"], self.new_name)

    def tearDown(self):
        try:
            delete_evaluator(self.new_name)
        except:
            pass
        try:
            delete_evaluator(self.original_name)
        except:
            pass


class TestListEvaluators(unittest.TestCase):
    def setUp(self):
        self.test_evaluator_name = "test_evaluator_list"
        self.test_evaluator_config = {
            "name": self.test_evaluator_name,
            "judge_models": "claude-3.5-sonnet@aws-bedrock",
        }
        create_evaluator(self.test_evaluator_config)

    def tearDown(self):
        try:
            delete_evaluator(self.test_evaluator_name)
        except:
            pass

    def test_list_evaluators(self):
        evaluators = list_evaluators()
        self.assertIsInstance(
            evaluators, list, f"Return type was not a list: {type(evaluators)}"
        )
        self.assertIn(
            self.test_evaluator_name,
            evaluators,
            f"Test evaluator not found in the list: {evaluators}",
        )
