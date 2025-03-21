import time

import unify
from unify.logging.utils import logs as _logs

from ..helpers import _handle_project


@_handle_project
def test_async_logger():
    start_time_sync = time.perf_counter()
    for i in range(50):
        unify.log(x=i, y=i * 2, z=i * 3)
    end_time_sync = time.perf_counter()

    unify.initialize_async_logger()
    start_time_async = time.perf_counter()
    for i in range(50):
        unify.log(x=i, y=i * 2, z=i * 3)

    # Wait for all logs to be submitted to be flushed
    while _logs._async_logger.queue.qsize() > 0:
        time.sleep(0.1)
    end_time_async = time.perf_counter()
    assert end_time_async - start_time_async < end_time_sync - start_time_sync
    assert _logs._async_logger.queue.qsize() == 0
    unify.shutdown_async_logger()
    assert unify.ASYNC_LOGGING == False


if __name__ == "__main__":
    pass
