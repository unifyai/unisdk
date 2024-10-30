import unify


def test_artifacts():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    artifacts = {"dataset": "my_dataset", "description": "this is my dataset"}
    assert len(unify.get_project_artifacts(project=project)) == 0
    unify.add_project_artifacts(project=project, **artifacts)
    assert "dataset" in unify.get_project_artifacts(project=project)
    unify.delete_project_artifact(
        "dataset",
        project=project,
    )
    assert "dataset" not in unify.get_project_artifacts(project=project)
    assert "description" in unify.get_project_artifacts(project=project)


if __name__ == "__main__":
    pass
