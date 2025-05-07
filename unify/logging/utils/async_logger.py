import asyncio
import logging
import os
import threading
from concurrent.futures import TimeoutError
from typing import List

import aiohttp

# Configure logging based on environment variable
ASYNC_LOGGER_DEBUG = os.getenv("UNIFY_ASYNC_LOGGER_DEBUG", "false").lower() in (
    "true",
    "1",
)
logger = logging.getLogger("async_logger")
logger.setLevel(logging.DEBUG if ASYNC_LOGGER_DEBUG else logging.WARNING)


class AsyncLoggerManager:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str = os.getenv("UNIFY_KEY"),
        num_consumers: int = 256,
    ):

        self.loop = asyncio.new_event_loop()
        self.queue = None
        self.consumers: List[asyncio.Task] = []
        self.num_consumers = num_consumers
        self.start_flag = threading.Event()
        self.shutting_down = False

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "accept": "application/json",
        }
        url = base_url + "/"
        connector = aiohttp.TCPConnector(limit=num_consumers // 2, loop=self.loop)
        self.session = aiohttp.ClientSession(
            url,
            headers=headers,
            loop=self.loop,
            connector=connector,
        )

        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.start_flag.wait()
        self.callbacks = []

    def register_callback(self, fn):
        self.callbacks.append(fn)

    def clear_callbacks(self):
        self.callbacks = []

    def _notify_callbacks(self):
        for fn in self.callbacks:
            fn()

    async def _join(self):
        await self.queue.join()

    def join(self):
        try:
            future = asyncio.run_coroutine_threadsafe(self._join(), self.loop)
            while True:
                try:
                    future.result(timeout=0.5)
                    break
                except (asyncio.TimeoutError, TimeoutError):
                    continue
        except Exception as e:
            logger.error(f"Error in join: {e}")
            raise e

    async def _main_loop(self):
        self.start_flag.set()
        await asyncio.gather(*self.consumers, return_exceptions=True)

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.queue = asyncio.Queue()

        for _ in range(self.num_consumers):
            self.consumers.append(self._log_consumer())

        try:
            self.loop.run_until_complete(self._main_loop())
        except Exception as e:
            logger.error(f"Event loop error: {e}")
            raise e
        finally:
            self.loop.close()

    async def _consume_create(self, body, future, idx):
        async with self.session.post("logs", json=body) as res:
            if res.status != 200:
                txt = await res.text()
                logger.error(f"Error in consume_create {idx}: {txt}")
                return
            res_json = await res.json()
            logger.debug(f"Created {idx} with response {res.status}: {res_json}")
            future.set_result(res_json[0])

    async def _consume_update(self, body, future, idx):
        if not future.done():
            await future
        body["logs"] = [future.result()]
        async with self.session.put("logs", json=body) as res:
            if res.status != 200:
                txt = await res.text()
                logger.error(f"Error in consume_update {idx}: {txt}")
                return
            res_json = await res.json()
            logger.debug(f"Updated {idx} with response {res.status}: {res_json}")

    async def _log_consumer(self):
        while True:
            try:
                event = await self.queue.get()
                idx = self.queue.qsize() + 1
                logger.debug(f"Processing event {event['type']}: {idx}")
                if event["type"] == "create":
                    await self._consume_create(event["_data"], event["future"], idx)
                elif event["type"] == "update":
                    await self._consume_update(event["_data"], event["future"], idx)
                else:
                    raise Exception(f"Unknown event type: {event['type']}")
            except Exception as e:
                event["future"].set_exception(e)
                logger.error(f"Error in consumer: {e}")
                raise e
            finally:
                self.queue.task_done()
                self._notify_callbacks()

    def log_create(
        self,
        project: str,
        context: str,
        params: dict,
        entries: dict,
    ) -> asyncio.Future:
        fut = self.loop.create_future()
        event = {
            "_data": {
                "project": project,
                "context": context,
                "params": params,
                "entries": entries,
            },
            "type": "create",
            "future": fut,
        }
        self.loop.call_soon_threadsafe(self.queue.put_nowait, event)
        return fut

    def log_update(
        self,
        project: str,
        context: str,
        future: asyncio.Future,
        mode: str,
        overwrite: bool,
        data: dict,
    ) -> None:
        event = {
            "_data": {
                mode: data,
                "project": project,
                "context": context,
                "overwrite": overwrite,
            },
            "type": "update",
            "future": future,
        }
        self.loop.call_soon_threadsafe(self.queue.put_nowait, event)

    def stop_sync(self, immediate=False):
        if self.shutting_down:
            return

        self.shutting_down = True
        if immediate:
            logger.debug("Stopping async logger immediately")
            self.loop.stop()
        else:
            self.join()
