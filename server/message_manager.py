from typing import Dict, Any
from .manager import ConnectionManager
from queue import Queue
from model.comm_protocol import Protocol


class ChipScannerMessageManager:
    def __init__(self, connection_manager: ConnectionManager):
        self.name = "Chip scanner manager"
        self.conn_manager = connection_manager
        self.request_queue = Queue()
        self.p = Protocol()

    async def process_message(self, data: Dict[str, Any], user_id: str):
        action = data[self.p.Labels.ACTION]
        if action == self.p.Actions.ADD_TO_QUEUE:  # "add_to_queue"
            await self.conn_manager.broadcast(
                {
                    self.p.Labels.ACTION: self.p.Actions.ADD_TO_QUEUE,
                    self.p.Labels.METADATA: {
                        self.p.Labels.USER: user_id,
                        self.p.Labels.REQUEST: data[self.p.Labels.METADATA],
                    },
                    self.p.Labels.STATUS_MSG: f"{user_id} added request {data[self.p.Labels.METADATA]}",
                    self.p.Labels.STATUS: self.p.Status.SUCCESS,
                }
            )
            self.request_queue.put(data[self.p.Labels.METADATA])
        if action == self.p.Actions.COLLECT_QUEUE:
            while not self.request_queue.empty():
                item = self.request_queue.get()
                print(f"Working on : {item}")
                print(f"Completed : {item}")
                await self.conn_manager.broadcast(
                    {
                        self.p.Labels.STATUS_MSG: f"Collecting request {item}",
                        self.p.Labels.STATUS: self.p.Status.SUCCESS,
                    }
                )
                self.request_queue.task_done()
        if action == self.p.Actions.CLEAR_QUEUE:
            with self.request_queue.mutex:
                self.request_queue.queue.clear()
            await self.conn_manager.broadcast(
                {
                    self.p.Labels.STATUS_MSG: f"{user_id} cleared queue",
                    self.p.Labels.ACTION: self.p.Actions.CLEAR_QUEUE,
                    self.p.Labels.METADATA: {self.p.Labels.USER: user_id},
                }
            )
