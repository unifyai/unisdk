import unittest

import unify


class TestCustomEndpoints(unittest.TestCase):
    def setUp(self):
        self.endpoint_name = "test_new_endpoint"
        self.new_endpoint_name = "renamed_test_new_endpoint"
        self.endpoint_url = "test.com"
        self.key_name = "test_key"
        self.key_value = "4321"
        unify.utils.custom_api_keys.create_custom_api_key(self.key_name, self.key_value)

    def test_custom_endpoints(self):
        unify.utils.custom_endpoints.create_custom_endpoint(
            self.endpoint_name, self.endpoint_url, self.key_name
        )
        unify.utils.custom_endpoints.list_custom_endpoints()
        unify.utils.custom_endpoints.rename_custom_endpoint(
            self.endpoint_name, self.new_endpoint_name
        )
        unify.utils.custom_endpoints.delete_custom_endpoint(self.new_endpoint_name)

    def tearDown(self):
        try:
            unify.utils.custom_api_keys.delete_custom_api_key(self.key_name)
        except:
            pass
        try:
            unify.utils.custom_api_keys.delete_custom_endpoint(self.endpoint_name)
        except:
            pass
        try:
            unify.utils.custom_api_keys.delete_custom_endpoint(self.new_endpoint_name)
        except:
            pass
