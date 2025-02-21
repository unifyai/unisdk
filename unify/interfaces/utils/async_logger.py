# async_logger.py
import asyncio
import logging
import os
import threading
import time

import aiohttp

# Configure logging based on environment variable
ASYNC_LOGGER_DEBUG = os.getenv("ASYNC_LOGGER_DEBUG", "").lower() == "true"
logger = logging.getLogger("async_logger")
logger.setLevel(logging.DEBUG if ASYNC_LOGGER_DEBUG else logging.WARNING)


class AsyncLoggerManager:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        batch_size: int = 100,
        flush_interval: float = 0.5,
        max_queue_size: int = 10000,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        # Use an asyncio queue instead of queue.Queue
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.running = False
        self.worker_thread = None
        self.session = None
        self._loop = None
        # Add an event to signal when loop is ready
        self._loop_ready = threading.Event()

        # Pre-build headers for convenience.
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "accept": "application/json",
        }

    def start(self):
        """Start the background worker thread."""
        if self.running:
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._async_worker, daemon=True)
        self.worker_thread.start()
        # Wait for the loop to be initialized
        self._loop_ready.wait()

    def stop(self):
        if not self.running:
            return

        self.running = False
        # Wait until the queue is flushed
        while not self.queue.empty():
            time.sleep(self.flush_interval)
        if self.worker_thread:
            # No need to call _flush_sync; the worker loop will flush remaining logs
            self.worker_thread.join()
            self.worker_thread = None

    def _safe_enqueue(self, event):
        if self.queue.full():
            try:
                dropped = self.queue.get_nowait()
                logger.debug("Queue full. Dropping oldest event: %s", dropped)
            except asyncio.QueueEmpty:
                pass
        self.queue.put_nowait(event)

    def log_create(
        self,
        project: str,
        context: str,
        params: dict,
        entries: dict,
    ) -> asyncio.Future:
        """
        Enqueue a log creation event and return a Future that will be resolved with the real log id.
        """
        if not self.running:
            raise RuntimeError("AsyncLoggerManager is not running")
        fut = self._loop.create_future()
        event = {
            "type": "create",
            "project": project,
            "context": context,
            "params": params,
            "entries": entries,
            "future": fut,
        }
        # Enqueue using the event loop's thread-safe call.
        self._loop.call_soon_threadsafe(self._safe_enqueue, event)
        return fut

    def log_update(
        self,
        project: str,
        context: str,
        log_future: asyncio.Future,
        mode: str,
        overwrite: bool,
        mutable,
        data: dict,
    ) -> None:
        """
        Enqueue a log update event.
        """
        if not self.running:
            raise RuntimeError("AsyncLoggerManager is not running")
        event = {
            "type": "update",
            "project": project,
            "context": context,
            "log_future": log_future,
            "mode": mode,
            "overwrite": overwrite,
            "mutable": mutable,
            "data": data,
        }
        self._loop.call_soon_threadsafe(self._safe_enqueue, event)

    def _async_worker(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        # Signal that the loop is ready
        self._loop_ready.set()

        async def _run_worker():
            async with aiohttp.ClientSession() as session:
                self.session = session
                # Continue until stopped and the queue is empty
                while self.running or not self.queue.empty():
                    await self._flush_async()
                    if self.running:  # only sleep if still running
                        await asyncio.sleep(self.flush_interval)

        self._loop.run_until_complete(_run_worker())
        self._loop.close()

    async def _flush_async(self):
        """Asynchronously flush batched events to the server."""
        events = []
        while not self.queue.empty() and len(events) < self.batch_size:
            try:
                event = self.queue.get_nowait()
                events.append(event)
            except asyncio.QueueEmpty:
                break

        if not events:
            return

        # --- Process create events ---
        create_events = [e for e in events if e["type"] == "create"]
        if create_events:
            grouped = {}
            for event in create_events:
                key = (event["project"], event["context"])
                if key not in grouped:
                    grouped[key] = {
                        "project": event["project"],
                        "context": event["context"],
                        "params": [],
                        "entries": [],
                        "futures": [],
                    }
                grouped[key]["params"].append(event["params"])
                grouped[key]["entries"].append(event["entries"])
                grouped[key]["futures"].append(event["future"])
            for group in grouped.values():
                try:
                    logger.debug("Creating logs with context %s", group["context"])
                    async with self.session.post(
                        f"{self.base_url}/logs",
                        json={
                            "project": group["project"],
                            "context": group["context"],
                            "params": group["params"],
                            "entries": group["entries"],
                        },
                        headers=self.headers,
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            for fut in group["futures"]:
                                if not fut.done():
                                    fut.set_exception(
                                        Exception(
                                            "Failed to create log: " + error_text,
                                        ),
                                    )
                        else:
                            json_resp = await response.json()
                            # Debug: log the response received
                            logger.debug("Received create response: %s", json_resp)
                            # Extract log id(s) based on the response format
                            if isinstance(json_resp, list):
                                log_ids = json_resp
                            elif isinstance(json_resp, dict):
                                # If the server returns a dict with key "log_ids"
                                if "log_ids" in json_resp:
                                    log_ids = json_resp["log_ids"]
                                # Otherwise, assume the dict itself is the id
                                else:
                                    log_ids = [json_resp]
                            else:
                                log_ids = [json_resp]  # assume single value
                            # Ensure we have as many ids as futures
                            if len(log_ids) < len(group["futures"]):
                                raise Exception(
                                    "Not enough log ids returned: " + str(json_resp),
                                )
                            for fut, log_id in zip(group["futures"], log_ids):
                                if not fut.done():
                                    fut.set_result(log_id)
                                    logger.debug("Set future result: %s", log_id)
                except Exception as e:
                    logger.error("Exception during log creation: %s", e)
                    for fut in group["futures"]:
                        if not fut.done():
                            fut.set_exception(e)

        # --- Process update events ---
        update_events = [e for e in events if e["type"] == "update"]
        if update_events:
            grouped = {}
            for event in update_events:
                # Ensure the log creation future is resolved (await if needed)
                try:
                    if not event["log_future"].done():
                        await event["log_future"]
                except Exception as e:
                    logger.error("Exception while awaiting log creation: %s", e)
                    continue  # Skip updates if log creation failed
                log_id = event["log_future"].result()
                key = (
                    event["project"],
                    event["context"],
                    event["mode"],
                    event["overwrite"],
                    str(event["mutable"]),
                    log_id,
                )
                if key not in grouped:
                    grouped[key] = {
                        "project": event["project"],
                        "context": event["context"],
                        "mode": event["mode"],
                        "overwrite": event["overwrite"],
                        "mutable": event["mutable"],
                        "log_ids": [],
                        "data": [],
                    }
                grouped[key]["log_ids"].append(log_id)
                grouped[key]["data"].append(event["data"])
            for group in grouped.values():
                try:
                    for data in group["data"]:
                        async with self.session.put(
                            f"{self.base_url}/logs",
                            json={
                                "ids": list(set(group["log_ids"])),
                                group["mode"]: data,
                                "overwrite": group["overwrite"],
                                "context": group["context"],
                            },
                            headers=self.headers,
                        ) as response:
                            if response.status != 200:
                                error_text = await response.text()
                                logger.error("Update failed: %s", error_text)
                except Exception as e:
                    logger.error("Exception during log update: %s", e)
