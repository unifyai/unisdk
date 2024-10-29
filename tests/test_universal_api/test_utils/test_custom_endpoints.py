import unittest

import unify


# noinspection PyBroadException
class CustomEndpointHandler:

    def __init__(self, key_name, key_value, endpoint_names):
        self._key_name = key_name
        self._key_value = key_value
        self._endpoint_names = endpoint_names

    def _handle(self):
        try:
            unify.delete_custom_api_key(self._key_name)
        except:
            pass
        for endpoint_name in self._endpoint_names:
            try:
                unify.delete_custom_endpoint(endpoint_name)
            except:
                pass
        unify.create_custom_api_key(self._key_name, self._key_value)

    def __enter__(self):
        self._handle()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._handle()


class TestCustomEndpoints(unittest.TestCase):

    def setUp(self):
        self.endpoint_name = "my_endpoint@custom"
        self.new_endpoint_name = "renamed@custom"
        self.endpoint_url = "test.com"
        self.key_name = "test_key"
        self.key_value = "4321"
        unify.create_custom_api_key(self.key_name, self.key_value)
        self._custom_endpoint_handler = CustomEndpointHandler(
            self.key_name,
            self.key_value,
            [self.endpoint_name, self.new_endpoint_name],
        )

    def test_create_custom_endpoint(self):
        with self._custom_endpoint_handler:
            unify.create_custom_endpoint(
                name=self.endpoint_name,
                url=self.endpoint_url,
                key_name=self.key_name,
            )

    def test_list_custom_endpoints(self):
        with self._custom_endpoint_handler:
            unify.create_custom_endpoint(
                name=self.endpoint_name,
                url=self.endpoint_url,
                key_name=self.key_name,
            )
            custom_endpoints = unify.list_custom_endpoints()
            assert len(custom_endpoints) == 1
            assert self.endpoint_name == custom_endpoints[0]["name"]

    def test_rename_custom_endpoint(self):
        with self._custom_endpoint_handler:
            unify.create_custom_endpoint(
                name=self.endpoint_name,
                url=self.endpoint_url,
                key_name=self.key_name,
            )
            custom_endpoints = unify.list_custom_endpoints()
            assert len(custom_endpoints) == 1
            assert self.endpoint_name == custom_endpoints[0]["name"]
            unify.rename_custom_endpoint(
                self.endpoint_name,
                self.new_endpoint_name,
            )
            custom_endpoints = unify.list_custom_endpoints()
            assert len(custom_endpoints) == 1
            assert self.new_endpoint_name == custom_endpoints[0]["name"]

    def test_delete_custom_endpoints(self):
        with self._custom_endpoint_handler:
            unify.create_custom_endpoint(
                name=self.endpoint_name,
                url=self.endpoint_url,
                key_name=self.key_name,
            )
            custom_endpoints = unify.list_custom_endpoints()
            assert len(custom_endpoints) == 1
            assert self.endpoint_name == custom_endpoints[0]["name"]
            unify.delete_custom_endpoint(self.endpoint_name)
            custom_endpoints = unify.list_custom_endpoints()
            assert len(custom_endpoints) == 0
