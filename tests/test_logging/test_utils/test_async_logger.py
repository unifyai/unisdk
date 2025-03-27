import unify

from ..helpers import _handle_project


@_handle_project
def test_async_logger():
    try:
        logs_sync = [unify.log(x=i, y=i * 2, z=i * 3) for i in range(10)]

        unify.initialize_async_logger()
        logs_async = [unify.log(x=i, y=i * 2, z=i * 3) for i in range(10)]
        unify.shutdown_async_logger()

        assert len(logs_async) == len(logs_sync)
        for log_async, log_sync in zip(
            sorted(logs_async, key=lambda x: x.entries["x"]),
            sorted(logs_sync, key=lambda x: x.entries["x"]),
        ):
            assert log_async.entries == log_sync.entries
        assert unify.ASYNC_LOGGING == False
    except Exception as e:
        unify.shutdown_async_logger()
        raise e


if __name__ == "__main__":
    pass
