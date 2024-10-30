import os

import unify

dir_path = os.path.dirname(os.path.realpath(__file__))


def test_with_logging() -> None:
    model_fn = lambda msg: "This is my response."
    model_fn = unify.with_logging(model_fn, endpoint="my_model")
    model_fn(msg="Hello?")


if __name__ == "__main__":
    pass
