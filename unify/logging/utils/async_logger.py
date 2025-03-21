# async_logger.py
import asyncio
import logging
import os
import threading
import time
from typing import List

import aiohttp

# Configure logging based on environment variable
ASYNC_LOGGER_DEBUG = os.getenv("ASYNC_LOGGER_DEBUG", "").lower() == "true"
logger = logging.getLogger("async_logger")
logger.addHandler(logging.FileHandler("async_logger.log", mode="w"))
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
        self.queue = asyncio.Queue()
        self.consumers: List[asyncio.Task] = []
        self.num_consumers = num_consumers
        self.shutdown_flag = threading.Event()
        self.start_flag = threading.Event()

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

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)

        for _ in range(self.num_consumers):
            task = asyncio.ensure_future(self._log_consumer(), loop=self.loop)
            self.consumers.append(task)

        if ASYNC_LOGGER_DEBUG:
            asyncio.ensure_future(self.queue_debugger(), loop=self.loop)

        try:
            self.start_flag.set()
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            self.loop.close()

    if ASYNC_LOGGER_DEBUG:

        async def queue_debugger(self):
            self.start_time = time.perf_counter()
            while True:
                logger.debug(
                    f"[{time.perf_counter() - self.start_time:.2f}] Remaining items in queue: {self.queue.qsize()}",
                )
                await asyncio.sleep(1)

    async def _consume_create(self, body, future):
        async with self.session.post("logs", json=body) as res:
            if res.status != 200:
                txt = await res.text()
                logger.error(f"Error in consume_create: {txt}")
                raise Exception(txt)
            res_json = await res.json()
            future.set_result(res_json[0])
            self.queue.task_done()

    async def _consume_update(self, body, future):
        if not future.done():
            await future
        body["ids"] = [future.result()]
        async with self.session.put("logs", json=body) as res:
            if res.status != 200:
                txt = await res.text()
                logger.error(f"Error in consume_update: {txt}")
                raise Exception(txt)
            self.queue.task_done()

    async def _log_consumer(self):
        while True:
            try:
                event = await self.queue.get()
                logger.debug(f"Got event: {event}")
                if event["type"] == "create":
                    await self._consume_create(event["_data"], event["future"])
                elif event["type"] == "update":
                    await self._consume_update(event["_data"], event["future"])
                else:
                    raise Exception(f"Unknown event type: {event['type']}")
            except Exception as e:
                logger.error(f"Error in consumer: {e}")
                self.queue.task_done()

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

    def stop_sync(self):
        while self.queue.qsize() > 0:
            time.sleep(0.1)
        self.loop.stop()
