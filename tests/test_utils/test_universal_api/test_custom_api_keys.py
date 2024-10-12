import unittest

import unify


# noinspection PyBroadException
class CustomAPIKeyHandler:

    def __init__(self, key_name, key_value, new_name):
        self._key_name = key_name
        self._key_value = key_value
        self._new_name = new_name

    def _handle(self):
        for name in (self._key_name, self._new_name):
            try:
                unify.delete_custom_api_key(name)
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


class TestCustomAPIKeys(unittest.TestCase):

    def setUp(self):
        self.key_name = "my_test_key2"
        self.key_value = "1234"
        self.new_name = "new_test_key"
        self._handler = CustomAPIKeyHandler(
            self.key_name, self.key_value, self.new_name
        )

    def test_create_custom_api_key(self):
        with self._handler:
            response = unify.create_custom_api_key(self.key_name, self.key_value)
            assert response == {"info": "API key created successfully!"}

    def test_list_custom_api_keys(self):
        with self._handler:
            custom_keys = unify.list_custom_api_keys()
            assert isinstance(custom_keys, list)
            assert len(custom_keys) == 0
            unify.create_custom_api_key(self.key_name, self.key_value)
            custom_keys = unify.list_custom_api_keys()
            assert isinstance(custom_keys, list)
            assert len(custom_keys) == 1
            assert custom_keys[0]["name"] == self.key_name
            assert custom_keys[0]["value"] == "*"*4 + self.key_value

    def test_get_custom_api_key(self):
        with self._handler:
            unify.create_custom_api_key(self.key_name, self.key_value)
            retrieved_key = unify.get_custom_api_key(self.key_name)
            assert isinstance(retrieved_key, dict)
            assert retrieved_key["name"] == self.key_name
            assert retrieved_key["value"] == "*"*4 + self.key_value

    def test_rename_custom_api_key(self):
        with self._handler:
            unify.create_custom_api_key(self.key_name, self.key_value)
            custom_keys = unify.list_custom_api_keys()
            assert isinstance(custom_keys, list)
            assert len(custom_keys) == 1
            assert custom_keys[0]["name"] == self.key_name
            unify.rename_custom_api_key(self.key_name, self.new_name)
            custom_keys = unify.list_custom_api_keys()
            assert isinstance(custom_keys, list)
            assert len(custom_keys) == 1
            assert custom_keys[0]["name"] == self.new_name

    def test_delete_custom_api_key(self):
        with self._handler:
            unify.create_custom_api_key(self.key_name, self.key_value)
            custom_keys = unify.list_custom_api_keys()
            assert isinstance(custom_keys, list)
            assert len(custom_keys) == 1
            assert custom_keys[0]["name"] == self.key_name
            unify.delete_custom_api_key(self.key_name)
            custom_keys = unify.list_custom_api_keys()
            assert isinstance(custom_keys, list)
            assert len(custom_keys) == 0
