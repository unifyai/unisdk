import unittest

import unify


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

    def test_custom_api_keys(self):
        unify.utils.custom_api_keys.create_custom_api_key(self.key_name, self.key_value)
        get_key = unify.utils.custom_api_keys.get_custom_api_key(self.key_name)
        self.assertTrue(get_key["value"].endswith(self.key_value))
        list_keys = unify.utils.custom_api_keys.list_custom_api_keys()
        self.assertTrue(_find_key(self.key_name, list_keys))

        unify.utils.custom_api_keys.rename_custom_api_key(self.key_name, self.new_name)
        list_keys = unify.utils.custom_api_keys.list_custom_api_keys()
        self.assertFalse(_find_key(self.key_name, list_keys))
        self.assertTrue(_find_key(self.new_name, list_keys))

    def tearDown(self):
        try:
            unify.utils.custom_api_keys.delete_custom_api_key(self.key_name)
        except:
            pass
        try:
            unify.utils.custom_api_keys.delete_custom_api_key(self.new_name)
        except:
            pass
