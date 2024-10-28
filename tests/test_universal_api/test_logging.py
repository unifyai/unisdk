import os
import unittest

import unify

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestLogging(unittest.TestCase):

    def test_with_logging(self) -> None:
        model_fn = lambda msg: "This is my response."
        model_fn = unify.with_logging(model_fn, endpoint="my_model")
        model_fn(msg="Hello?")
