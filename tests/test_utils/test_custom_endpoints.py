import unittest

import unify


class CustomEndpointHandler:

    def __init__(self, key_name, endpoint_names):
        self._key_name = key_name
        self._endpoint_names = endpoint_names

    def _handle(self):
        if self._key_name in unify.list_custom_api_keys():
            unify.delete_custom_api_key(self._key_name)
        for endpoint_name in self._endpoint_names:
            if endpoint_name in [ep["name"] for ep in unify.list_custom_endpoints()]:
                unify.delete_custom_endpoint(endpoint_name)

    def __enter__(self):
        self._handle()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._handle()


class TestCustomEndpoints(unittest.TestCase):

    def setUp(self):
        self.endpoint_name = "test_new_endpoint"
        self.new_endpoint_name = "renamed_test_new_endpoint"
        self.endpoint_url = "test.com"
        self.key_name = "test_key"
        self.key_value = "4321"
        unify.create_custom_api_key(self.key_name, self.key_value)
        self._custom_endpoint_handler = CustomEndpointHandler(
            self.key_name, [self.endpoint_name, self.new_endpoint_name]
        )

    def test_create_custom_endpoint(self):
        with self._custom_endpoint_handler:
            unify.create_custom_endpoint(
                self.endpoint_name, self.endpoint_url, self.key_name
            )

    def test_list_custom_endpoints(self):
        with self._custom_endpoint_handler:
            unify.create_custom_endpoint(
                self.endpoint_name, self.endpoint_url, self.key_name
            )
            custom_endpoints = unify.list_custom_endpoints()
            assert len(custom_endpoints) == 1
            assert self.endpoint_name == custom_endpoints[0]["name"]

    def test_rename_custom_endpoint(self):
        with self._custom_endpoint_handler:
            unify.create_custom_endpoint(
                self.endpoint_name, self.endpoint_url, self.key_name
            )
            custom_endpoints = unify.list_custom_endpoints()
            assert len(custom_endpoints) == 1
            assert self.endpoint_name == custom_endpoints[0]["name"]
            unify.rename_custom_endpoint(
                self.endpoint_name, self.new_endpoint_name
            )
            custom_endpoints = unify.list_custom_endpoints()
            assert len(custom_endpoints) == 1
            assert self.new_endpoint_name == custom_endpoints[0]["name"]

    def test_delete_custom_endpoints(self):
        with self._custom_endpoint_handler:
            unify.create_custom_endpoint(
                self.endpoint_name, self.endpoint_url, self.key_name
            )
            custom_endpoints = unify.list_custom_endpoints()
            assert len(custom_endpoints) == 1
            assert self.endpoint_name == custom_endpoints[0]["name"]
            unify.delete_custom_endpoint(self.endpoint_name)
            custom_endpoints = unify.list_custom_endpoints()
            assert len(custom_endpoints) == 0
