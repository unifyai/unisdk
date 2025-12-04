import unify

from ..helpers import _handle_project


@_handle_project
def test_create_context():
    assert len(unify.get_contexts()) == 0
    unify.create_context("my_context")
    assert len(unify.get_contexts()) == 1
    assert "my_context" in unify.get_contexts()


@_handle_project
def test_create_contexts_names_only():
    assert len(unify.get_contexts()) == 0
    unify.create_contexts(["foo", "bar"])
    assert len(unify.get_contexts()) == 2
    assert "foo" in unify.get_contexts()
    assert "bar" in unify.get_contexts()


@_handle_project
def test_create_contexts_dicts():
    assert len(unify.get_contexts()) == 0
    unify.create_contexts(
        [
            {"name": "foo", "description": "bar"},
            {"name": "bar", "description": "baz"},
        ],
    )
    assert len(unify.get_contexts()) == 2
    assert "foo" in unify.get_contexts()
    assert "bar" in unify.get_contexts()

    assert unify.get_context("foo")["description"] == "bar"
    assert unify.get_context("bar")["description"] == "baz"


@_handle_project
def test_create_contexts_nested():
    unify.create_contexts(
        [
            "foo",
            "foo/bar",
            "foo/bar/baz",
        ],
    )
    assert len(unify.get_contexts()) == 3
    assert "foo" in unify.get_contexts()
    assert "foo/bar" in unify.get_contexts()
    assert "foo/bar/baz" in unify.get_contexts()

    unify.delete_context("foo")

    assert len(unify.get_contexts()) == 0

    # Reverse order should work as well
    unify.create_contexts(
        [
            "foo/bar/baz",
            "foo/bar",
            "foo",
        ],
    )
    assert len(unify.get_contexts()) == 3
    assert "foo" in unify.get_contexts()
    assert "foo/bar" in unify.get_contexts()
    assert "foo/bar/baz" in unify.get_contexts()


@_handle_project
def test_get_contexts():
    assert len(unify.get_contexts()) == 0
    unify.log(x=0, context="a/b")
    unify.log(x=1, context="a/b")
    unify.log(x=0, context="b/c")
    unify.log(x=1, context="b/c")
    contexts = unify.get_contexts()
    assert len(contexts) == 2
    assert "a/b" in contexts
    assert "b/c" in contexts
    contexts = unify.get_contexts(prefix="a")
    assert len(contexts) == 1
    assert "a/b" in contexts
    assert "a/c" not in contexts
    contexts = unify.get_contexts(prefix="b")
    assert len(contexts) == 1
    assert "b/c" in contexts
    assert "a/b" not in contexts


@_handle_project
def test_delete_context():
    unify.log(x=0, context="a/b")
    contexts = unify.get_contexts()
    assert len(contexts) == 1
    assert "a/b" in contexts
    unify.delete_context("a/b")
    assert "a/b" not in unify.get_contexts()
    assert len(unify.get_logs()) == 0


@_handle_project
def test_add_logs_to_context():
    l0 = unify.log(x=0, context="a/b")
    l1 = unify.log(x=1, context="a/b")
    l2 = unify.log(x=2, context="b/c")
    l3 = unify.log(x=3, context="b/c")
    unify.add_logs_to_context(log_ids=[l0.id, l1.id], context="b/c")
    assert len(unify.get_logs(context="a/b")) == 2
    assert unify.get_logs(context="a/b", return_ids_only=True) == [l1.id, l0.id]
    assert len(unify.get_logs(context="b/c")) == 4
    assert unify.get_logs(context="b/c", return_ids_only=True) == [
        l3.id,
        l2.id,
        l1.id,
        l0.id,
    ]


@_handle_project
def test_rename_context():
    unify.log(x=0, context="a/b")
    unify.rename_context("a/b", "a/c")
    contexts = unify.get_contexts()
    assert "a/b" not in contexts
    assert "a/c" in contexts
    logs = unify.get_logs(context="a/c")
    assert len(logs) == 1
    assert logs[0].context == "a/c"


@_handle_project
def test_get_context():
    name = "foo"
    desc = "my_description"
    is_versioned = True
    allow_duplicates = True
    unify.create_context(
        name,
        description=desc,
        is_versioned=is_versioned,
        allow_duplicates=allow_duplicates,
    )

    context = unify.get_context(name)
    assert context["name"] == name
    assert context["description"] == desc
    assert context["is_versioned"] is is_versioned
    assert context["allow_duplicates"] is allow_duplicates


@_handle_project
def test_context_nesting():
    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == ""
    assert current_ctx["write"] == ""

    with unify.Context("A"):
        current_ctx = unify.get_active_context()
        assert current_ctx["read"] == "A"
        assert current_ctx["write"] == "A"
        assert unify.get_context(current_ctx["read"])["name"] == "A"
        assert unify.get_context(current_ctx["write"])["name"] == "A"

        with unify.Context("B"):
            current_ctx = unify.get_active_context()
            assert current_ctx["read"] == "A/B"
            assert current_ctx["write"] == "A/B"
            assert unify.get_context(current_ctx["read"])["name"] == "A/B"
            assert unify.get_context(current_ctx["write"])["name"] == "A/B"

    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == ""
    assert current_ctx["write"] == ""


@_handle_project
def test_context_relative():
    unify.set_context("A", relative=True)

    unify.set_context("B", relative=True)
    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == "A/B"
    assert current_ctx["write"] == "A/B"
    assert unify.get_context(current_ctx["read"])["name"] == "A/B"

    unify.set_context("C", relative=True)
    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == "A/B/C"
    assert current_ctx["write"] == "A/B/C"
    assert unify.get_context(current_ctx["read"])["name"] == "A/B/C"


@_handle_project
def test_context_not_relative():
    unify.set_context("A", relative=False)
    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == "A"
    assert current_ctx["write"] == "A"
    assert unify.get_context(current_ctx["read"])["name"] == "A"

    unify.set_context("B", relative=False)
    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == "B"
    assert current_ctx["write"] == "B"
    assert unify.get_context(current_ctx["read"])["name"] == "B"


@_handle_project
def test_create_context_with_foreign_keys():
    """Test creating a context with foreign key definitions."""
    # Create referenced context
    unify.create_context(
        name="Departments",
        description="Department master data",
        unique_keys={"id": "int"},
        auto_counting={"id": None},
    )

    # Create context with foreign key
    unify.create_context(
        name="Employees",
        description="Employee data",
        foreign_keys=[
            {
                "name": "department_id",
                "references": "Departments.id",
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            },
        ],
    )

    # Verify foreign key is stored
    context = unify.get_context("Employees")
    assert context["name"] == "Employees"
    assert "foreign_keys" in context
    assert len(context["foreign_keys"]) == 1
    assert context["foreign_keys"][0]["name"] == "department_id"
    assert context["foreign_keys"][0]["references"] == "Departments.id"
    assert context["foreign_keys"][0]["on_delete"] == "CASCADE"
    assert context["foreign_keys"][0]["on_update"] == "CASCADE"


@_handle_project
def test_create_context_with_multiple_foreign_keys():
    """Test creating a context with multiple foreign keys."""
    # Create referenced contexts
    unify.create_context(
        name="Departments",
        unique_keys={"id": "int"},
        auto_counting={"id": None},
    )
    unify.create_context(
        name="Managers",
        unique_keys={"id": "int"},
        auto_counting={"id": None},
    )

    # Create context with multiple foreign keys
    unify.create_context(
        name="Employees",
        foreign_keys=[
            {
                "name": "department_id",
                "references": "Departments.id",
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            },
            {
                "name": "manager_id",
                "references": "Managers.id",
                "on_delete": "SET NULL",
                "on_update": "CASCADE",
            },
        ],
    )

    # Verify both foreign keys are stored
    context = unify.get_context("Employees")
    assert len(context["foreign_keys"]) == 2

    fk_names = {fk["name"] for fk in context["foreign_keys"]}
    assert "department_id" in fk_names
    assert "manager_id" in fk_names

    # Check specific foreign key details
    dept_fk = next(
        fk for fk in context["foreign_keys"] if fk["name"] == "department_id"
    )
    assert dept_fk["references"] == "Departments.id"
    assert dept_fk["on_delete"] == "CASCADE"

    mgr_fk = next(fk for fk in context["foreign_keys"] if fk["name"] == "manager_id")
    assert mgr_fk["references"] == "Managers.id"
    assert mgr_fk["on_delete"] == "SET NULL"


@_handle_project
def test_create_contexts_batch_with_foreign_keys():
    """Test batch creation of contexts with foreign keys."""
    unify.create_contexts(
        [
            {
                "name": "Departments",
                "description": "Department master data",
                "unique_keys": {"id": "int"},
                "auto_counting": {"id": None},
            },
            {
                "name": "Employees",
                "description": "Employee data",
                "foreign_keys": [
                    {
                        "name": "department_id",
                        "references": "Departments.id",
                        "on_delete": "CASCADE",
                        "on_update": "CASCADE",
                    },
                ],
            },
        ],
    )

    # Verify both contexts were created
    contexts = unify.get_contexts()
    assert "Departments" in contexts
    assert "Employees" in contexts

    # Verify foreign key on Employees context
    employee_context = unify.get_context("Employees")
    assert len(employee_context["foreign_keys"]) == 1
    assert employee_context["foreign_keys"][0]["name"] == "department_id"


@_handle_project
def test_create_context_without_foreign_keys():
    """Test that contexts without foreign keys still work (backward compatibility)."""
    unify.create_context(
        name="SimpleContext",
        description="A context without foreign keys",
    )

    context = unify.get_context("SimpleContext")
    assert context["name"] == "SimpleContext"
    assert "foreign_keys" in context
    assert context["foreign_keys"] == []


@_handle_project
def test_foreign_key_cascade_action():
    """Test CASCADE action on foreign key."""
    # Create parent context with data
    unify.create_context(
        name="Departments",
        unique_keys={"dept_id": "int"},
        auto_counting={"dept_id": None},
    )
    dept_log = unify.log(dept_name="Engineering", context="Departments")

    # Create child context with CASCADE foreign key
    unify.create_context(
        name="Employees",
        foreign_keys=[
            {
                "name": "department_id",
                "references": "Departments.dept_id",
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            },
        ],
    )

    # Get the department id from the log
    dept_logs = unify.get_logs(context="Departments")
    assert len(dept_logs) == 1
    # Access the auto-counted dept_id field from _entries
    dept_id = dept_logs[0]._entries.get("dept_id")

    # Create employee referencing department
    emp_log = unify.log(
        emp_name="Alice",
        department_id=dept_id,
        context="Employees",
    )

    # Verify employee was created
    emp_logs = unify.get_logs(context="Employees")
    assert len(emp_logs) == 1


@_handle_project
def test_foreign_key_set_null_action():
    """Test SET NULL action on foreign key."""
    # Create parent context
    unify.create_context(
        name="Departments",
        unique_keys={"id": "int"},
        auto_counting={"id": None},
    )

    # Create child context with SET NULL foreign key
    unify.create_context(
        name="Employees",
        foreign_keys=[
            {
                "name": "department_id",
                "references": "Departments.id",
                "on_delete": "SET NULL",
                "on_update": "SET NULL",
            },
        ],
    )

    # Verify the foreign key configuration
    context = unify.get_context("Employees")
    assert context["foreign_keys"][0]["on_delete"] == "SET NULL"
    assert context["foreign_keys"][0]["on_update"] == "SET NULL"


@_handle_project
def test_nested_contexts_with_foreign_keys():
    """Test foreign keys work with nested context names."""
    # Create nested parent context
    unify.create_context(
        name="org/departments",
        unique_keys={"id": "int"},
        auto_counting={"id": None},
    )

    # Create nested child context with foreign key
    unify.create_context(
        name="org/employees",
        foreign_keys=[
            {
                "name": "department_id",
                "references": "org/departments.id",
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            },
        ],
    )

    # Verify foreign key references nested context correctly
    context = unify.get_context("org/employees")
    assert context["foreign_keys"][0]["references"] == "org/departments.id"


@_handle_project
def test_flat_array_foreign_key():
    """Test foreign key with flat array notation (tag_ids[*])."""
    # Create referenced context for tags
    unify.create_context(
        name="Tags",
        unique_keys={"tag_id": "int"},
        auto_counting={"tag_id": None},
    )

    # Create context with flat array FK
    unify.create_context(
        name="Articles",
        description="Articles with multiple tag references",
        foreign_keys=[
            {
                "name": "tag_ids[*]",
                "references": "Tags.tag_id",
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            },
        ],
    )

    # Verify FK is stored with nested path
    context = unify.get_context("Articles")
    assert "foreign_keys" in context
    assert len(context["foreign_keys"]) == 1

    fk = context["foreign_keys"][0]
    assert fk["name"] == "tag_ids[*]"
    assert fk["references"] == "Tags.tag_id"
    assert fk["on_delete"] == "CASCADE"

    # Verify is_nested flag is set
    assert fk.get("is_nested") is True

    # Verify path_segments are populated (flat array has 1 segment)
    assert "path_segments" in fk
    assert len(fk["path_segments"]) == 1
    assert fk["path_segments"][0]["name"] == "tag_ids"
    assert fk["path_segments"][0]["is_array"] is True
    assert fk["path_segments"][0]["is_wildcard"] is True


@_handle_project
def test_nested_array_foreign_key():
    """Test foreign key with nested array notation (images[*].image_id)."""
    # Create referenced context for images
    unify.create_context(
        name="Images",
        unique_keys={"image_id": "int"},
        auto_counting={"image_id": None},
    )

    # Create context with nested array FK
    unify.create_context(
        name="Transcripts",
        description="Transcripts with multiple image references",
        foreign_keys=[
            {
                "name": "images[*].image_id",
                "references": "Images.image_id",
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            },
        ],
    )

    # Verify FK is stored with nested path
    context = unify.get_context("Transcripts")
    assert "foreign_keys" in context
    assert len(context["foreign_keys"]) == 1

    fk = context["foreign_keys"][0]
    assert fk["name"] == "images[*].image_id"
    assert fk["references"] == "Images.image_id"
    assert fk["on_delete"] == "CASCADE"

    # Verify is_nested flag is set
    assert fk.get("is_nested") is True

    # Verify path_segments are populated
    assert "path_segments" in fk
    assert len(fk["path_segments"]) == 2
    assert fk["path_segments"][0]["name"] == "images"
    assert fk["path_segments"][0]["is_array"] is True
    assert fk["path_segments"][1]["name"] == "image_id"


@_handle_project
def test_nested_object_foreign_key():
    """Test foreign key with nested object path (metadata.user.user_id)."""
    # Create referenced context for users
    unify.create_context(
        name="Users",
        unique_keys={"user_id": "int"},
        auto_counting={"user_id": None},
    )

    # Create context with nested object FK
    unify.create_context(
        name="Records",
        description="Records with nested user metadata",
        foreign_keys=[
            {
                "name": "metadata.user.user_id",
                "references": "Users.user_id",
                "on_delete": "SET NULL",
                "on_update": "CASCADE",
            },
        ],
    )

    # Verify FK is stored with nested path
    context = unify.get_context("Records")
    assert "foreign_keys" in context
    assert len(context["foreign_keys"]) == 1

    fk = context["foreign_keys"][0]
    assert fk["name"] == "metadata.user.user_id"
    assert fk["references"] == "Users.user_id"
    assert fk["on_delete"] == "SET NULL"

    # Verify is_nested flag is set
    assert fk.get("is_nested") is True

    # Verify path_segments are populated
    assert "path_segments" in fk
    assert len(fk["path_segments"]) == 3
    assert fk["path_segments"][0]["name"] == "metadata"
    assert fk["path_segments"][0]["is_array"] is False
    assert fk["path_segments"][1]["name"] == "user"
    assert fk["path_segments"][2]["name"] == "user_id"


@_handle_project
def test_mixed_nesting_foreign_key():
    """Test foreign key with mixed array and object nesting (teams[*].members[*].user_id)."""
    # Create referenced context for users
    unify.create_context(
        name="Users",
        unique_keys={"user_id": "int"},
        auto_counting={"user_id": None},
    )

    # Create context with mixed nested FK
    unify.create_context(
        name="Projects",
        description="Projects with nested team structure",
        foreign_keys=[
            {
                "name": "teams[*].members[*].user_id",
                "references": "Users.user_id",
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            },
        ],
    )

    # Verify FK is stored with nested path
    context = unify.get_context("Projects")
    assert "foreign_keys" in context
    assert len(context["foreign_keys"]) == 1

    fk = context["foreign_keys"][0]
    assert fk["name"] == "teams[*].members[*].user_id"
    assert fk["references"] == "Users.user_id"
    assert fk["on_delete"] == "CASCADE"

    # Verify is_nested flag is set
    assert fk.get("is_nested") is True

    # Verify path_segments are populated
    assert "path_segments" in fk
    assert len(fk["path_segments"]) == 3

    # Check teams[*] segment
    assert fk["path_segments"][0]["name"] == "teams"
    assert fk["path_segments"][0]["is_array"] is True
    assert fk["path_segments"][0]["is_wildcard"] is True

    # Check members[*] segment
    assert fk["path_segments"][1]["name"] == "members"
    assert fk["path_segments"][1]["is_array"] is True
    assert fk["path_segments"][1]["is_wildcard"] is True

    # Check user_id segment
    assert fk["path_segments"][2]["name"] == "user_id"
    assert fk["path_segments"][2]["is_array"] is False


@_handle_project
def test_flat_array_fk_with_actual_data():
    """Test creating logs with flat array FK and verifying FK validation works."""
    # Create Tags context
    unify.create_context(
        name="Tags",
        unique_keys={"tag_id": "int"},
        auto_counting={"tag_id": None},
    )

    # Create Articles context with flat array FK
    unify.create_context(
        name="Articles",
        foreign_keys=[
            {
                "name": "tag_ids[*]",
                "references": "Tags.tag_id",
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            },
        ],
    )

    # Create some tags
    tag1 = unify.log(name="Python", context="Tags")
    tag2 = unify.log(name="ML", context="Tags")

    # Get the auto-generated tag_ids from _entries
    tags = unify.get_logs(context="Tags")
    tag1_id = tags[1]._entries.get("tag_id")  # Note: reversed order
    tag2_id = tags[0]._entries.get("tag_id")

    # Create article with valid flat array FK references
    article = unify.log(
        title="Introduction to ML",
        tag_ids=[tag1_id, tag2_id],  # Flat array of primitive values
        context="Articles",
    )

    # Verify article was created successfully
    articles = unify.get_logs(context="Articles")
    assert len(articles) == 1
    assert articles[0]._entries.get("title") == "Introduction to ML"
    assert len(articles[0]._entries.get("tag_ids")) == 2
    assert tag1_id in articles[0]._entries.get("tag_ids")
    assert tag2_id in articles[0]._entries.get("tag_ids")


@_handle_project
def test_nested_array_fk_with_actual_data():
    """Test creating logs with nested array FK and verifying FK validation works."""
    # Create Images context
    unify.create_context(
        name="Images",
        unique_keys={"image_id": "int"},
        auto_counting={"image_id": None},
    )

    # Create Transcripts context with nested array FK
    unify.create_context(
        name="Transcripts",
        foreign_keys=[
            {
                "name": "images[*].image_id",
                "references": "Images.image_id",
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            },
        ],
    )

    # Create some images
    img1 = unify.log(url="https://example.com/1.jpg", context="Images")
    img2 = unify.log(url="https://example.com/2.jpg", context="Images")

    # Get the auto-generated image_ids from _entries
    images = unify.get_logs(context="Images")
    img1_id = images[1]._entries.get("image_id")  # Note: reversed order
    img2_id = images[0]._entries.get("image_id")

    # Create transcript with valid nested FK references
    transcript = unify.log(
        transcript_id="t_001",
        images=[
            {"image_id": img1_id, "caption": "First image"},
            {"image_id": img2_id, "caption": "Second image"},
        ],
        context="Transcripts",
    )

    # Verify transcript was created successfully
    transcripts = unify.get_logs(context="Transcripts")
    assert len(transcripts) == 1
    assert transcripts[0]._entries.get("transcript_id") == "t_001"
    assert len(transcripts[0]._entries.get("images")) == 2


@_handle_project
def test_delete_context_prefix_collision():
    """Test that delete_context uses path-based matching, not simple string prefix.

    This verifies that deleting "test_call" does NOT delete "test_call_to_sms"
    (a sibling with shared string prefix), but DOES delete "test_call/Events"
    (an actual path child).
    """
    # Create contexts that share a string prefix but are siblings (not parent/child)
    unify.create_contexts(
        [
            "test_call",
            "test_call_to_sms",
            "test_call_to_email",
        ],
    )

    # Create actual path children of test_call
    unify.create_contexts(
        [
            "test_call/Events",
            "test_call/Logs",
        ],
    )

    assert len(unify.get_contexts()) == 5

    # Delete with delete_children=True should delete test_call and its path children,
    # but NOT the siblings that share a string prefix
    unify.delete_context("test_call", delete_children=True)

    contexts = unify.get_contexts()
    assert len(contexts) == 2
    # Siblings should still exist
    assert "test_call_to_sms" in contexts
    assert "test_call_to_email" in contexts
    # Parent and path children should be deleted
    assert "test_call" not in contexts
    assert "test_call/Events" not in contexts
    assert "test_call/Logs" not in contexts


@_handle_project
def test_delete_context_without_children():
    """Test that delete_children=False only deletes the exact context."""
    unify.create_contexts(
        [
            "parent",
            "parent/child1",
            "parent/child2",
        ],
    )

    assert len(unify.get_contexts()) == 3

    # Delete with delete_children=False should only delete the exact context
    unify.delete_context("parent", delete_children=False)

    contexts = unify.get_contexts()
    assert len(contexts) == 2
    assert "parent" not in contexts
    # Children should still exist
    assert "parent/child1" in contexts
    assert "parent/child2" in contexts


if __name__ == "__main__":
    pass
