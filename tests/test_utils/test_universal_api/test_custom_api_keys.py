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
        self.key_value = "4321"
        self.new_name = "new_test_key"
        self._handler = CustomAPIKeyHandler(
            self.key_name, self.key_value, self.new_name
        )

    def test_custom_api_keys(self):
        with self._handler:
            unify.create_custom_api_key(self.key_name, self.key_value)
            get_key = unify.get_custom_api_key(self.key_name)
            self.assertTrue(get_key["value"].endswith(self.key_value))
            list_keys = unify.list_custom_api_keys()
            self.assertTrue(_find_key(self.key_name, list_keys))

            unify.rename_custom_api_key(self.key_name, self.new_name)
            list_keys = unify.list_custom_api_keys()
            self.assertFalse(_find_key(self.key_name, list_keys))
            self.assertTrue(_find_key(self.new_name, list_keys))
