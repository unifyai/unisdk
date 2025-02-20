import asyncio
import queue
import threading
import warnings
from typing import Any, Dict, List

import aiohttp


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

        # Initialize queue and state
        self.queue = queue.Queue(maxsize=max_queue_size)
        self.running = False
        self.worker_thread = None
        self.session = None
        self._loop = None

    def start(self):
        """Start the background worker thread."""
        if self.running:
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._async_worker, daemon=True)
        self.worker_thread.start()

    def stop(self):
        if not self.running:
            return

        self.running = False
        if self.worker_thread:
            # No need to call _flush_sync; the worker loop will flush remaining logs
            self.worker_thread.join()
            self.worker_thread = None

    def log(
        self,
        project: str,
        context: str,
        params: Dict[str, Any],
        entries: List[Dict[str, Any]],
    ) -> None:
        """Add a log message to the queue."""
        if not self.running:
            raise RuntimeError("AsyncLoggerManager is not running")

        log_entry = {
            "project": project,
            "context": context,
            "params": params,
            "entries": entries,
        }

        try:
            self.queue.put(log_entry, block=False)
        except queue.Full:
            # Handle queue full condition by implementing the drop oldest strategy
            try:
                self.queue.get_nowait()
                warnings.warn("Warning: log queue full. Dropping oldest log entry")
                self.queue.put(log_entry, block=False)
            except queue.Empty:
                pass

    def _async_worker(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

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
        """Asynchronously flush batched logs to the server."""
        if self.queue.empty():
            return

        # Collect logs up to batch size
        batch = []
        while len(batch) < self.batch_size and not self.queue.empty():
            try:
                batch.append(self.queue.get_nowait())
            except queue.Empty:
                break

        if not batch:
            return

        # Group logs by project and context
        grouped_logs = {}
        for log in batch:
            key = (log["project"], log["context"])

            if key not in grouped_logs:
                grouped_logs[key] = {
                    "project": log["project"],
                    "context": log["context"],
                    "params": [],
                    "entries": [],
                }
            grouped_logs[key]["params"].append(log["params"])
            grouped_logs[key]["entries"].append(log["entries"])

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Send each grouped batch
        for group_data in grouped_logs.values():
            try:
                async with self.session.post(
                    f"{self.base_url}/logs",
                    json={
                        "project": group_data["project"],
                        "context": group_data["context"],
                        "params": group_data["params"],
                        "entries": group_data["entries"],
                    },
                    headers=headers,
                ) as response:
                    if response.status != 200:
                        raise Exception("Failed to flush logs", response.text)
            except Exception as e:
                print("exception: ", e)

    def _flush_sync(self):
        """Synchronously flush remaining logs during shutdown."""
        remaining_logs = []
        while not self.queue.empty():
            try:
                remaining_logs.append(self.queue.get_nowait())
            except queue.Empty:
                break

        if not remaining_logs:
            return

        # Create a new event loop for synchronous flush
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _flush_remaining():
            async with aiohttp.ClientSession() as session:
                self.session = session
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                # Group remaining logs by project and context
                for i in range(0, len(remaining_logs), self.batch_size):
                    batch = remaining_logs[i : i + self.batch_size]

                    # Group logs by project and context
                    grouped_logs = {}
                    for log in batch:
                        key = (log["project"], log["context"])
                        if key not in grouped_logs:
                            grouped_logs[key] = {
                                "project": log["project"],
                                "context": log["context"],
                                "params": [],
                                "entries": [],
                            }
                        grouped_logs[key]["params"].append(log["params"])
                        grouped_logs[key]["entries"].append(log["entries"])

                    # Send each grouped batch
                    for group_data in grouped_logs.values():
                        try:
                            async with session.post(
                                f"{self.base_url}/logs",
                                json={
                                    "project": group_data["project"],
                                    "context": group_data["context"],
                                    "params": group_data["params"],
                                    "entries": group_data["entries"],
                                },
                                headers=headers,
                            ) as response:
                                if response.status != 200:
                                    # Could add error logging here
                                    raise Exception(
                                        "Failed to flush logs",
                                        response.status,
                                    )
                        except Exception as e:
                            print("exception: ", e)

        loop.run_until_complete(_flush_remaining())
        loop.close()
