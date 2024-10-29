import unittest

import unify


class TestArtifacts(unittest.TestCase):

    def test_artifacts(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        artifacts = {"dataset": "my_dataset", "description": "this is my dataset"}
        assert len(unify.get_artifacts(project)) == 0
        unify.add_artifacts(project=project, **artifacts)
        assert "dataset" in unify.get_artifacts(project)
        unify.delete_artifact(
            "dataset",
            project,
        )
        assert "dataset" not in unify.get_artifacts(project)
        assert "description" in unify.get_artifacts(project)
