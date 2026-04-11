"""Tests for AsyncLoggerManager non-blocking guarantees.

The core contract of AsyncLoggerManager is that `log_create` and
`log_update` are fire-and-forget: they hand work to a background thread
and return ~immediately, never blocking the calling thread.

These tests verify that contract by calling `log_create` from an asyncio
event loop and asserting it doesn't stall the loop.  The current
implementation violates this because it calls
`asyncio.run_coroutine_threadsafe(...).result()` which blocks the
calling thread until the private loop processes the queue put.
"""

import asyncio
import subprocess
import sys
import time

import unify
from unify._async_logger import AsyncLoggerManager

from .helpers import TEST_PROJECT

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_logger(
    num_consumers: int = 4,
    max_queue_size: int = 10000,
) -> AsyncLoggerManager:
    return AsyncLoggerManager(
        name="test",
        num_consumers=num_consumers,
        max_queue_size=max_queue_size,
    )


def _ensure_project():
    if TEST_PROJECT not in unify.list_projects():
        unify.create_project(TEST_PROJECT)
    unify.activate(TEST_PROJECT)


CTX = "test_async_logger/bench"
DEADLINE_MS = 50


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLogCreateIsNonBlocking:
    """log_create must return in <50ms regardless of consumer/queue state."""

    def test_log_create_baseline(self):
        """Baseline: single call with idle queue returns quickly."""
        _ensure_project()
        logger = _make_logger()
        try:
            t0 = time.perf_counter()
            fut = logger.log_create(
                project=TEST_PROJECT,
                context=CTX,
                entries={"msg": "hello"},
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            assert (
                elapsed_ms < DEADLINE_MS
            ), f"log_create took {elapsed_ms:.0f}ms (limit {DEADLINE_MS}ms)"
            assert fut is not None
        finally:
            logger.stop_sync(immediate=True)

    def test_log_create_with_full_queue(self):
        """log_create must not block the caller when the queue is full.

        Uses max_queue_size=1 so the queue fills after the first item.
        The second log_create will find the queue full; with the current
        implementation, `asyncio.Queue.put()` awaits until space is
        available, and `.result()` blocks the calling thread for that
        entire duration.

        A correct implementation would use a thread-safe queue with
        put_nowait (raising or dropping on full) instead of blocking.
        """
        _ensure_project()
        logger = _make_logger(num_consumers=1, max_queue_size=1)
        try:
            # First call succeeds (queue was empty) — don't even time it
            logger.log_create(
                project=TEST_PROJECT,
                context=CTX,
                entries={"i": 0},
            )
            # The consumer is now busy with an HTTP call. Queue may be full.
            # Give consumer a moment to pick up the item but not finish the HTTP call
            time.sleep(0.05)

            # Flood: these should be instant (drop or enqueue without blocking)
            timings = []
            for i in range(5):
                t0 = time.perf_counter()
                logger.log_create(
                    project=TEST_PROJECT,
                    context=CTX,
                    entries={"i": i + 1},
                )
                timings.append((time.perf_counter() - t0) * 1000)

            max_ms = max(timings)
            assert max_ms < DEADLINE_MS, (
                f"log_create blocked for {max_ms:.0f}ms when queue was full "
                f"(limit {DEADLINE_MS}ms). Timings: "
                f"{[f'{t:.0f}ms' for t in timings]}"
            )
        finally:
            logger.stop_sync(immediate=True)

    def test_log_create_does_not_block_asyncio_loop(self):
        """log_create called from inside asyncio.run() must not block the loop.

        Fills the queue first to ensure `queue.put()` has to wait, then
        calls log_create from a coroutine.  The `.result()` call freezes
        the entire event loop until the private loop drains an item.
        """
        _ensure_project()
        logger = _make_logger(num_consumers=1, max_queue_size=1)

        # Fill the queue from outside the loop
        logger.log_create(
            project=TEST_PROJECT,
            context=CTX,
            entries={"phase": "prefill"},
        )
        time.sleep(0.05)

        async def _measure():
            t0 = time.perf_counter()
            logger.log_create(
                project=TEST_PROJECT,
                context=CTX,
                entries={"phase": "from_loop"},
            )
            return (time.perf_counter() - t0) * 1000

        try:
            elapsed_ms = asyncio.run(_measure())
            assert elapsed_ms < DEADLINE_MS, (
                f"log_create blocked the event loop for {elapsed_ms:.0f}ms "
                f"(limit {DEADLINE_MS}ms)"
            )
        finally:
            logger.stop_sync(immediate=True)

    def test_rapid_log_create_does_not_starve_event_loop(self):
        """Rapid log_create calls must not starve other coroutines.

        Simulates the Unity EventBus pattern: a coroutine publishes
        events (calling log_create) while other coroutines need the loop.
        With a small queue, each log_create blocks the loop while waiting
        for space, starving asyncio.sleep(0).
        """
        _ensure_project()
        logger = _make_logger(num_consumers=2, max_queue_size=2)

        async def _run():
            stop = asyncio.Event()

            async def _publisher():
                i = 0
                while not stop.is_set():
                    logger.log_create(
                        project=TEST_PROJECT,
                        context=CTX,
                        entries={"i": i},
                    )
                    i += 1
                    await asyncio.sleep(0)

            task = asyncio.create_task(_publisher())
            # Let publisher saturate the queue
            await asyncio.sleep(0.5)

            latencies = []
            for _ in range(5):
                t0 = time.perf_counter()
                await asyncio.sleep(0)
                latencies.append((time.perf_counter() - t0) * 1000)

            stop.set()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            return latencies

        try:
            latencies = asyncio.run(_run())
            avg_ms = sum(latencies) / len(latencies)
            max_ms = max(latencies)

            assert avg_ms < DEADLINE_MS, (
                f"avg asyncio.sleep(0) was {avg_ms:.0f}ms during rapid "
                f"log_create (limit {DEADLINE_MS}ms) — log_create is "
                f"blocking the event loop. Latencies: "
                f"{[f'{t:.0f}ms' for t in latencies]}"
            )
        finally:
            logger.stop_sync(immediate=True)


class TestLogUpdateIsNonBlocking:
    """log_update has the same `.result()` pattern and the same issue."""

    def test_log_update_with_full_queue(self):
        """log_update must not block when the queue is full."""
        _ensure_project()
        logger = _make_logger(num_consumers=1, max_queue_size=1)

        try:
            create_fut = logger.log_create(
                project=TEST_PROJECT,
                context=CTX,
                entries={"msg": "original"},
            )
            time.sleep(0.05)

            t0 = time.perf_counter()
            logger.log_update(
                project=TEST_PROJECT,
                context=CTX,
                future=create_fut,
                overwrite=True,
                data={"msg": "updated"},
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000

            assert elapsed_ms < DEADLINE_MS, (
                f"log_update took {elapsed_ms:.0f}ms with full queue "
                f"(limit {DEADLINE_MS}ms)"
            )
        finally:
            logger.stop_sync(immediate=True)


class TestGracefulShutdown:
    """Process exit must not hang when atexit handlers run."""

    def test_single_logger_exits_cleanly(self):
        """A process with one AsyncLoggerManager should exit within 3s."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import time; "
                    "from unify._async_logger import AsyncLoggerManager; "
                    "l = AsyncLoggerManager(name='t', num_consumers=16); "
                    "time.sleep(0.5)"
                ),
            ],
            timeout=3,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_multiple_loggers_exit_cleanly(self):
        """A process with two AsyncLoggerManagers should exit within 3s."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import time; "
                    "from unify._async_logger import AsyncLoggerManager; "
                    "l1 = AsyncLoggerManager(name='a', num_consumers=16); "
                    "l2 = AsyncLoggerManager(name='b', num_consumers=16); "
                    "time.sleep(0.5)"
                ),
            ],
            timeout=3,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
