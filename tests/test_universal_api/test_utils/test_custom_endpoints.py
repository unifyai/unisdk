import unify


# noinspection PyBroadException
class CustomEndpointHandler:
    def __init__(self, ky_name, ky_value, endpoint_names):
        self._key_name = ky_name
        self._key_value = ky_value
        self._endpoint_names = endpoint_names

    def _handle(self):
        try:
            unify.delete_custom_api_key(self._key_name)
        except:
            pass
        for endpoint_nm in self._endpoint_names:
            try:
                unify.delete_custom_endpoint(endpoint_nm)
            except:
                pass
        unify.create_custom_api_key(self._key_name, self._key_value)

    def __enter__(self):
        self._handle()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._handle()


endpoint_name = "my_endpoint@custom"
new_endpoint_name = "renamed@custom"
endpoint_url = "test.com"
key_name = "test_key"
key_value = "4321"
unify.create_custom_api_key(key_name, key_value)
custom_endpoint_handler = CustomEndpointHandler(
    key_name,
    key_value,
    [endpoint_name, new_endpoint_name],
)


def test_create_custom_endpoint():
    with custom_endpoint_handler:
        unify.create_custom_endpoint(
            name=endpoint_name,
            url=endpoint_url,
            key_name=key_name,
        )


def test_list_custom_endpoints():
    with custom_endpoint_handler:
        unify.create_custom_endpoint(
            name=endpoint_name,
            url=endpoint_url,
            key_name=key_name,
        )
        custom_endpoints = unify.list_custom_endpoints()
        assert len(custom_endpoints) == 1
        assert endpoint_name == custom_endpoints[0]["name"]


def test_rename_custom_endpoint():
    with custom_endpoint_handler:
        unify.create_custom_endpoint(
            name=endpoint_name,
            url=endpoint_url,
            key_name=key_name,
        )
        custom_endpoints = unify.list_custom_endpoints()
        assert len(custom_endpoints) == 1
        assert endpoint_name == custom_endpoints[0]["name"]
        unify.rename_custom_endpoint(
            endpoint_name,
            new_endpoint_name,
        )
        custom_endpoints = unify.list_custom_endpoints()
        assert len(custom_endpoints) == 1
        assert new_endpoint_name == custom_endpoints[0]["name"]


def test_delete_custom_endpoints():
    with custom_endpoint_handler:
        unify.create_custom_endpoint(
            name=endpoint_name,
            url=endpoint_url,
            key_name=key_name,
        )
        custom_endpoints = unify.list_custom_endpoints()
        assert len(custom_endpoints) == 1
        assert endpoint_name == custom_endpoints[0]["name"]
        unify.delete_custom_endpoint(endpoint_name)
        custom_endpoints = unify.list_custom_endpoints()
        assert len(custom_endpoints) == 0


if __name__ == "__main__":
    pass
