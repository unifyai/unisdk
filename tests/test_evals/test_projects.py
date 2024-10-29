import unittest

import unify


class TestProjectScope(unittest.TestCase):

    def test_set_project(self):
        unify.deactivate()
        self.assertIs(unify.active_project, None)
        unify.activate("my_project")
        self.assertEqual(unify.active_project, "my_project")
        unify.deactivate()

    def test_unset_project(self):
        unify.deactivate()
        self.assertIs(unify.active_project, None)
        unify.activate("my_project")
        self.assertEqual(unify.active_project, "my_project")
        unify.deactivate()
        self.assertIs(unify.active_project, None)

    def test_with_project(self):
        unify.deactivate()
        self.assertIs(unify.active_project, None)
        with unify.Project("my_project"):
            self.assertEqual(unify.active_project, "my_project")
        self.assertIs(unify.active_project, None)

    def test_set_project_then_log(self):
        unify.deactivate()
        self.assertIs(unify.active_project, None)
        unify.activate("my_project")
        self.assertEqual(unify.active_project, "my_project")
        unify.log(key=1.0)
        unify.deactivate()
        self.assertIs(unify.active_project, None)
        with self.assertRaises(Exception):
            unify.log(key=1.0)

    def test_with_project_then_log(self):
        unify.deactivate()
        self.assertIs(unify.active_project, None)
        with unify.Project("my_project"):
            self.assertEqual(unify.active_project, "my_project")
            unify.log(key=1.0)
        self.assertIs(unify.active_project, None)
        with self.assertRaises(Exception):
            unify.log(key=1.0)
