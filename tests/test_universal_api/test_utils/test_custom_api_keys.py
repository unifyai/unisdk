import unify


# noinspection PyBroadException
class CustomAPIKeyHandler:
    def __init__(self, ky_name, ky_value, nw_name):
        self._key_name = ky_name
        self._key_value = ky_value
        self._new_name = nw_name

    def _handle(self):
        # should work even if list_custom_api_keys does not
        for name in (self._key_name, self._new_name):
            try:
                unify.delete_custom_api_key(name)
            except:
                pass
        # should if other keys have wrongly been created
        try:
            custom_keys = unify.list_custom_api_keys()
            for dct in custom_keys:
                unify.delete_custom_api_key(dct["name"])
        except:
            pass

    def __enter__(self):
        self._handle()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._handle()


def _find_key(key_to_find, list_of_keys):
    for key in list_of_keys:
        if key["name"] == key_to_find:
            return True
    return False


key_name = "my_test_key2"
key_value = "1234"
new_name = "new_test_key"
handler = CustomAPIKeyHandler(
    key_name,
    key_value,
    new_name,
)


def test_create_custom_api_key():
    with handler:
        response = unify.create_custom_api_key(key_name, key_value)
        assert response == {"info": "API key created successfully!"}


def test_list_custom_api_keys():
    with handler:
        custom_keys = unify.list_custom_api_keys()
        assert isinstance(custom_keys, list)
        assert len(custom_keys) == 0
        unify.create_custom_api_key(key_name, key_value)
        custom_keys = unify.list_custom_api_keys()
        assert isinstance(custom_keys, list)
        assert len(custom_keys) == 1
        assert custom_keys[0]["name"] == key_name
        assert custom_keys[0]["value"] == "*" * 4 + key_value


def test_get_custom_api_key():
    with handler:
        unify.create_custom_api_key(key_name, key_value)
        retrieved_key = unify.get_custom_api_key(key_name)
        assert isinstance(retrieved_key, dict)
        assert retrieved_key["name"] == key_name
        assert retrieved_key["value"] == "*" * 4 + key_value


def test_rename_custom_api_key():
    with handler:
        unify.create_custom_api_key(key_name, key_value)
        custom_keys = unify.list_custom_api_keys()
        assert isinstance(custom_keys, list)
        assert len(custom_keys) == 1
        assert custom_keys[0]["name"] == key_name
        unify.rename_custom_api_key(key_name, new_name)
        custom_keys = unify.list_custom_api_keys()
        assert isinstance(custom_keys, list)
        assert len(custom_keys) == 1
        assert custom_keys[0]["name"] == new_name


def test_delete_custom_api_key():
    with handler:
        unify.create_custom_api_key(key_name, key_value)
        custom_keys = unify.list_custom_api_keys()
        assert isinstance(custom_keys, list)
        assert len(custom_keys) == 1
        assert custom_keys[0]["name"] == key_name
        unify.delete_custom_api_key(key_name)
        custom_keys = unify.list_custom_api_keys()
        assert isinstance(custom_keys, list)
        assert len(custom_keys) == 0


if __name__ == "__main__":
    pass
