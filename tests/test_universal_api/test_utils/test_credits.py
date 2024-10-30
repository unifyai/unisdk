import unify


def test_get_credits() -> None:
    creds = unify.get_credits()
    assert isinstance(creds, float)


if __name__ == "__main__":
    pass
