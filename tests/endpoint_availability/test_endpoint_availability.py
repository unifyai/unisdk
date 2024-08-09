import unify
import unittest


class TestEndpoints(unittest.TestCase):

    def test_list_models(self) -> None:
        models = unify.utils.list_models()
        assert isinstance(models, list), "return type was not a list: {}".format(
            models
        )  # is list
        assert models, "returned list was empty: {}".format(models)  # not empty
        assert len(models) == len(set(models)), "duplication detected: {}".format(
            models
        )  # no duplication

    def test_list_providers(self) -> None:
        providers = unify.utils.list_providers()
        assert isinstance(providers, list), "return type was not a list: {}".format(
            providers
        )  # is list
        assert providers, "returned list was empty: {}".format(providers)  # not empty
        assert len(providers) == len(set(providers)), "duplication detected: {}".format(
            providers
        )  # no duplication

    def test_list_endpoints(self) -> None:
        endpoints = unify.utils.list_endpoints()
        assert isinstance(endpoints, list), "return type was not a list: {}".format(
            endpoints
        )  # is list
        assert endpoints, "returned list was empty: {}".format(endpoints)  # not empty
        assert len(endpoints) == len(set(endpoints)), "duplication detected: {}".format(
            endpoints
        )  # no duplication
