import unify
import unittest


class TestVersioning(unittest.TestCase):

    @staticmethod
    def my_func():
        a = 1 + 2
        b = a + 3
        return b

    def test_get_code(self):
        assert (
            unify.get_code(self.my_func)
            == "    @staticmethod\n    def my_func():\n        a = 1 + 2\n        "
            "b = a + 3\n        return b\n"
        )

    def test_versioned(self):
        system_prompt = unify.versioned("you are an expert")
        assert system_prompt.version == 0
        assert system_prompt.value == "you are an expert"
        system_prompt.update("you are an expert mathematician")
        assert system_prompt.version == 1
        assert system_prompt.value == "you are an expert mathematician"
        assert len(system_prompt) == 2
        assert system_prompt.at_version(0).value == "you are an expert"
        assert system_prompt.value == "you are an expert mathematician"
        system_prompt.set_version(0)
        assert system_prompt.value == "you are an expert"

    def test_double_versioned(self):
        system_prompt = unify.versioned(unify.versioned("you are an expert"))
        assert system_prompt.version == 0
        assert system_prompt.value == "you are an expert"

    def test_versioned_from_upstream(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        unify.activate(project)
        unify.log(system_prompt=unify.versioned("you are an expert", 0))
        system_prompt = unify.Versioned.from_upstream("system_prompt")
        assert system_prompt.version == 0
        assert system_prompt.value == "you are an expert"
        unify.log(system_prompt=unify.versioned("you are an expert mathematician", 1))
        assert len(system_prompt) == 1
        system_prompt.download()
        assert len(system_prompt) == 2
        assert system_prompt.at_version(0).value == "you are an expert"
        assert system_prompt.value == "you are an expert mathematician"
        system_prompt.set_version(0)
        assert system_prompt.value == "you are an expert"

    def test_versioned_sync(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        unify.activate(project)
        # versioned and logged v0
        unify.log(system_prompt=unify.versioned("you are an expert", 0))
        # logged v1 without version
        unify.log(system_prompt="you are an expert dude")
        # versioned v1 locally
        system_prompt = unify.versioned("you are an expert dude", 1)
        # v1 not upstream
        logs = unify.get_logs(project)
        assert logs[0].entries == {"system_prompt/0": "you are an expert"}
        assert logs[1].entries == {"system_prompt": "you are an expert dude"}
        system_prompt.sync("system_prompt")
        # v1 now upstream after sync
        logs = unify.get_logs(project)
        assert logs[0].entries == {"system_prompt/0": "you are an expert"}
        assert logs[1].entries == {"system_prompt/1": "you are an expert dude"}

    def test_add_version(self):
        system_prompt = unify.versioned("you are an expert")
        assert system_prompt.version == 0
        assert system_prompt.value == "you are an expert"
        system_prompt.add_version(1, "you are an expert mathematician")
        assert len(system_prompt) == 2

    def test_set_latest(self):
        system_prompt = unify.versioned("you are an expert")
        assert system_prompt.version == 0
        assert system_prompt.value == "you are an expert"
        system_prompt.add_version(1, "you are an expert mathematician")
        assert len(system_prompt) == 2
        system_prompt.set_latest()
        assert system_prompt.version == 1
        assert system_prompt.value == "you are an expert mathematician"

    def test_versioned_contains(self):
        system_prompt = unify.versioned("you are an expert")
        assert 0 in system_prompt
        system_prompt.update("you are an expert mathematician")
        assert 1 in system_prompt
        assert 2 not in system_prompt
