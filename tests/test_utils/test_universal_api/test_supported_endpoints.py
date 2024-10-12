import unify
import unittest


class TestSupportedModels(unittest.TestCase):

    def setUp(self):
        self._all_endpoints = unify.list_endpoints()

    def test_list_models(self) -> None:
        models = unify.list_models()
        assert isinstance(models, list), "return type was not a list: {}".format(
            models
        )  # is list
        assert models, "returned list was empty: {}".format(models)  # not empty
        assert len(models) == len(set(models)), "duplication detected: {}".format(
            models
        )  # no duplication

    def test_list_models_w_provider(self):
        models = unify.list_models("openai")
        assert isinstance(models, list), "return type was not a list: {}".format(
            models
        )  # is list
        assert models, "returned list was empty: {}".format(models)  # not empty
        assert len(models) == len(set(models)), "duplication detected: {}".format(
            models
        )  # no duplication
        assert len(models) == len([e for e in self._all_endpoints if "openai" in e]), \
            ("number of models for the provider did not match the number of endpoints "
             "with the provider in the string")


class TestSupportedProviders(unittest.TestCase):

    def setUp(self):
        self._all_endpoints = unify.list_endpoints()

    def test_list_providers(self) -> None:
        providers = unify.list_providers()
        assert isinstance(providers, list), "return type was not a list: {}".format(
            providers
        )  # is list
        assert providers, "returned list was empty: {}".format(providers)  # not empty
        assert len(providers) == len(set(providers)), "duplication detected: {}".format(
            providers
        )  # no duplication

    def test_list_providers_w_model(self):
        providers = unify.list_providers("llama-3.2-90b-chat")
        assert isinstance(providers, list), "return type was not a list: {}".format(
            providers
        )  # is list
        assert providers, "returned list was empty: {}".format(providers)  # not empty
        assert len(providers) == len(set(providers)), "duplication detected: {}".format(
            providers
        )  # no duplication
        assert len(providers) == len([
            e for e in self._all_endpoints if "llama-3.2-90b-chat" in e
        ]), ("number of providers for the model did not match the number of endpoints "
             "with the model in the string")


class TestSupportedEndpoints(unittest.TestCase):

    def setUp(self):
        self._all_endpoints = unify.list_endpoints()

    def test_list_endpoints(self) -> None:
        endpoints = unify.list_endpoints()
        assert isinstance(endpoints, list), "return type was not a list: {}".format(
            endpoints
        )  # is list
        assert endpoints, "returned list was empty: {}".format(endpoints)  # not empty
        assert len(endpoints) == len(set(endpoints)), "duplication detected: {}".format(
            endpoints
        )  # no duplication

    def test_list_endpoints_w_model(self) -> None:
        endpoints = unify.list_endpoints(model="llama-3.2-90b-chat")
        assert isinstance(endpoints, list), "return type was not a list: {}".format(
            endpoints
        )  # is list
        assert endpoints, "returned list was empty: {}".format(endpoints)  # not empty
        assert len(endpoints) == len(set(endpoints)), "duplication detected: {}".format(
            endpoints
        )  # no duplication
        assert len(endpoints) == len(unify.list_providers("llama-3.2-90b-chat")), \
            ("number of endpoints for the model did not match the number of providers "
             "for the model")

    def test_list_endpoints_w_provider(self) -> None:
        endpoints = unify.list_endpoints(provider="openai")
        assert isinstance(endpoints, list), "return type was not a list: {}".format(
            endpoints
        )  # is list
        assert endpoints, "returned list was empty: {}".format(endpoints)  # not empty
        assert len(endpoints) == len(set(endpoints)), "duplication detected: {}".format(
            endpoints
        )  # no duplication
        assert len(endpoints) == len(unify.list_models("openai")), \
            ("number of endpoints for the provider did not match the number of models "
             "for the provider")

    def test_list_endpoints_w_model_w_provider(self) -> None:
        with self.assertRaises(Exception):
            unify.list_endpoints("gpt-4o", "openai")
