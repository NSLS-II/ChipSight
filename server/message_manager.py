from typing import Dict, Any
from .manager import ConnectionManager
from queue import Queue
from model.comm_protocol import Protocol

# from server import start_bs


class ChipScannerMessageManager:
    def __init__(self, connection_manager: ConnectionManager):
        self.name = "Chip scanner manager"
        self.conn_manager = connection_manager
        self.request_queue = Queue()
        self.p = Protocol()

    async def process_message(self, data: Dict[str, Any], user_id: str):
        action = data[self.p.Key.ACTION]
        if action == self.p.Action.ADD_TO_QUEUE:
            await self.add_to_queue(data, user_id)
        elif action == self.p.Action.COLLECT_QUEUE:
            await self.collect_queue(data, user_id)
        elif action == self.p.Action.CLEAR_QUEUE:
            await self.clear_queue(data, user_id)
        elif action == self.p.Key.MOVE_GONIO:
            await self.move_gonio(data, user_id)

    """
    Other unimplemented commands:
     - Pause queue: Should complete current task and pause
     - Stop queue: Stop current task immediately 
     - Run immediately: E.g. click to center
    """

    async def move_gonio(self, data: Dict[str, Any], user_id: str):
        """
        start_bs.gonio2.move_gonio(data[self.p.Key.METADATA]["x"],
                                   data[self.p.Key.METADATA]["y"],
                                   data[self.p.Key.METADATA]["z"])

        """

        await self.conn_manager.broadcast(
            {
                self.p.Key.STATUS_MSG: f"{user_id} moved gonio to {data[self.p.Key.METADATA]}",
                self.p.Key.STATUS: self.p.Status.SUCCESS,
            }
        )

    async def add_to_queue(self, data: Dict[str, Any], user_id: str):
        """
        Adds request to queue, then broadcasts to all clients that a request has been added
        """

        self.request_queue.put(data[self.p.Key.METADATA])
        # Move light temporary testing only!

        await self.conn_manager.broadcast(
            {
                self.p.Key.ACTION: self.p.Action.ADD_TO_QUEUE,
                self.p.Key.METADATA: {
                    self.p.Key.USER: user_id,
                    self.p.Key.REQUEST: data[self.p.Key.METADATA],
                },
                self.p.Key.STATUS_MSG: f"{user_id} added request {data[self.p.Key.METADATA]}",
                self.p.Key.STATUS: self.p.Status.SUCCESS,
            }
        )

    async def collect_queue(self, data: Dict[str, Any], user_id: str):
        """
        Runs all tasks in the queue. Ideally will be excuted by the BlueSky run engine
        """
        while not self.request_queue.empty():
            item = self.request_queue.get()
            print(f"Working on : {item}")
            print(f"Completed : {item}")
            await self.conn_manager.broadcast(
                {
                    self.p.Key.STATUS_MSG: f"Collecting request {item}",
                    self.p.Key.STATUS: self.p.Status.SUCCESS,
                }
            )
            self.request_queue.task_done()

    async def clear_queue(self, data: Dict[str, Any], user_id: str):
        """
        Removes all pending tasks from the queue
        """
        with self.request_queue.mutex:
            self.request_queue.queue.clear()
        await self.conn_manager.broadcast(
            {
                self.p.Key.STATUS_MSG: f"{user_id} cleared queue",
                self.p.Key.ACTION: self.p.Action.CLEAR_QUEUE,
                self.p.Key.METADATA: {self.p.Key.USER: user_id},
            }
        )

    async def send_login_result(self, success: bool, username: str, client_id: str):
        if success:
            data = {
                self.p.Key.LOGIN: self.p.Status.SUCCESS,
                self.p.Key.STATUS_MSG: f"Successfully logged in as {username}",
            }
        else:
            data = {self.p.Key.LOGIN: self.p.Status.FAILURE}
        await self.conn_manager.unicast(data, client_id)
