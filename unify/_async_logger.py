import asyncio
import atexit
import logging
import os
import queue as _stdlib_queue
import threading
from typing import List

import aiohttp

from unify import BASE_URL
from unify.utils.helpers import _create_request_header

# Configure logging based on environment variable
ASYNC_LOGGER_DEBUG = os.getenv("UNIFY_ASYNC_LOGGER_DEBUG", "false").lower() in (
    "true",
    "1",
)


class AsyncLoggerManager:
    def __init__(
        self,
        *,
        name: str = "unknown",
        base_url: str = BASE_URL,
        api_key: str = os.getenv("UNIFY_KEY"),
        num_consumers: int = 256,
        max_queue_size: int = 10000,
    ):
        self.name = f"UnifyAsyncLogger.{name}"
        self.loop = asyncio.new_event_loop()
        self.queue = None
        self.consumers: List[asyncio.Task] = []
        self.num_consumers = num_consumers
        self.start_flag = threading.Event()
        self.shutting_down = False
        self.thread_raised_exception = threading.Event()
        self.max_queue_size = max_queue_size
        self.logger = logging.getLogger(self.name)
        if ASYNC_LOGGER_DEBUG:
            self.logger.setLevel(logging.DEBUG)

        # Register shutdown handler
        atexit.register(self.stop_sync, immediate=False)

        headers = _create_request_header(api_key)
        url = base_url + "/"
        connector = aiohttp.TCPConnector(limit=num_consumers // 2, loop=self.loop)
        self.session = aiohttp.ClientSession(
            url,
            headers=headers,
            loop=self.loop,
            connector=connector,
        )

        self.thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name=self.name,
        )
        self.thread.start()
        self.start_flag.wait()
        if self.thread_raised_exception.is_set():
            raise RuntimeError(f"{self.name} thread failed to start")
        self.callbacks = []

    def register_callback(self, fn):
        self.callbacks.append(fn)

    def clear_callbacks(self):
        self.callbacks = []

    def _notify_callbacks(self):
        for fn in self.callbacks:
            fn()

    def join(self):
        """Block until every enqueued item has been processed."""
        if self.queue is None:
            return
        self.queue.join()

    async def _main_loop(self):
        self.start_flag.set()
        self.logger.debug(f"Spawning {self.num_consumers} consumers")
        await asyncio.gather(*self.consumers, return_exceptions=True)

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.queue = _stdlib_queue.Queue(maxsize=self.max_queue_size)

        for _ in range(self.num_consumers):
            self.consumers.append(self._log_consumer())

        try:
            self.loop.run_until_complete(self._main_loop())
        except Exception as e:
            self.shutting_down = True
            self.thread_raised_exception.set()
            self.start_flag.set()
            raise e
        finally:
            self.loop.close()

    async def _consume_create(self, body, future, idx):
        async with self.session.post("logs", json=body) as res:
            if res.status != 200:
                txt = await res.text()
                self.logger.error(
                    f"Failed to create log {idx} {res.status}: {txt}",
                )
                return
            res_json = await res.json()
            self.logger.debug(
                f"Created log {res_json['log_event_ids'][0]} with status {res.status}",
            )
            future.set_result(res_json["log_event_ids"][0])

    async def _consume_update(self, body, future, idx):
        if not future.done():
            await future
        body["logs"] = [future.result()]
        async with self.session.put("logs", json=body) as res:
            if res.status != 200:
                txt = await res.text()
                self.logger.error(
                    f"Failed to update log {idx} {body['logs'][0]} {res.status}: {txt}",
                )
                return
            res_json = await res.json()
            self.logger.debug(
                f"Updated log {res_json['log_event_ids'][0]} with status {res.status}",
            )

    _SENTINEL = object()

    def _blocking_get(self):
        """Blocking get with periodic timeout so consumers can exit on shutdown."""
        import concurrent.futures.thread as _cft

        _interpreter_exiting = getattr(_cft, "_shutdown", False)

        while True:
            try:
                return self.queue.get(timeout=0.5)
            except _stdlib_queue.Empty:
                _interpreter_exiting = getattr(_cft, "_shutdown", False)
                if self.shutting_down or _interpreter_exiting:
                    return self._SENTINEL
                continue

    async def _log_consumer(self):
        loop = asyncio.get_event_loop()
        while True:
            event = None
            try:
                event = await loop.run_in_executor(None, self._blocking_get)
                if event is self._SENTINEL:
                    return
                idx = self.queue.qsize() + 1
                self.logger.debug(f"'{event['type']}' processing {idx}")
                if event["type"] == "create":
                    await self._consume_create(event["_data"], event["future"], idx)
                elif event["type"] == "update":
                    await self._consume_update(event["_data"], event["future"], idx)
                else:
                    raise Exception(f"Unknown event type: {event['type']}")
            except RuntimeError as e:
                if "shutdown" in str(e).lower():
                    return
                raise
            except Exception as e:
                if self.shutting_down:
                    return
                if event is not None and event is not self._SENTINEL:
                    try:
                        event["future"].set_exception(e)
                    except Exception:
                        pass
                self.logger.error(f"Error in consumer: {e}")
                raise e
            finally:
                if event is not None and event is not self._SENTINEL:
                    self.queue.task_done()
                    self._notify_callbacks()

    def log_create(
        self,
        project: str,
        context: str,
        entries: dict,
    ) -> asyncio.Future:
        if self.shutting_down:
            self.logger.warning("Not running, skipping log create")
            return None
        fut = self.loop.create_future()
        event = {
            "_data": {
                "project_name": project,
                "context": context,
                "entries": entries,
            },
            "type": "create",
            "future": fut,
        }
        try:
            self.queue.put_nowait(event)
        except _stdlib_queue.Full:
            self.logger.debug("Queue full, dropping log create")
            return None
        return fut

    def log_update(
        self,
        project: str,
        context: str,
        future: asyncio.Future,
        overwrite: bool,
        data: dict,
    ) -> None:
        if self.shutting_down:
            self.logger.warning("Not running, skipping log update")
            return
        event = {
            "_data": {
                "entries": data,
                "project_name": project,
                "context": context,
                "overwrite": overwrite,
            },
            "type": "update",
            "future": future,
        }
        try:
            self.queue.put_nowait(event)
        except _stdlib_queue.Full:
            self.logger.debug("Queue full, dropping log update")

    def clear_queue(self):
        if self.queue is None:
            return

        orig_size = self.queue.qsize()
        while True:
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except _stdlib_queue.Empty:
                break
        self.logger.debug(f"{orig_size} log requests cleared")

    def stop_sync(self, immediate=False):
        if self.shutting_down:
            self.logger.debug("Already shutting down, skipping stop")
            return

        self.shutting_down = True
        if immediate:
            self.logger.debug("Shutting down immediately")
            self.loop.stop()
        else:
            self.logger.debug("Shutting down gracefully")
            self.join()
