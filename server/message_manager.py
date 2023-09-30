from typing import Dict, Any, Callable
from .manager import ConnectionManager
from queue import Queue
from model.comm_protocol import Protocol

from server import start_bs


class ChipScannerMessageManager:
    def __init__(self, connection_manager: ConnectionManager):
        self.name = "Chip scanner manager"
        self.conn_manager = connection_manager
        self.request_queue = Queue()

    async def process_message(self, data: Dict[str, Any], user_id: str):
        action = data[Protocol.Key.ACTION]
        action_methods: Dict[str, Callable] = {
            Protocol.Action.ADD_TO_QUEUE: self.add_to_queue,
            Protocol.Action.COLLECT_QUEUE: self.collect_queue,
            Protocol.Action.CLEAR_QUEUE: self.clear_queue,
            Protocol.Action.MOVE_GONIO: self.move_gonio,
            Protocol.Action.NUDGE_GONIO: self.nudge_gonio,
            Protocol.Action.SET_FIDUCIAL: self.set_fiducial,
            Protocol.Action.GO_TO_FIDUCIAL: self.go_to_fiducial,
        }
        # If co-routines become complicated or need more than just data and user_id
        # consider using match statements for python>=3.10
        method = action_methods.get(action, self.unrecognized_action)
        await method(data, user_id)

    """
    Other unimplemented commands:
     - Pause queue: Should complete current task and pause
     - Stop queue: Stop current task immediately 
     - Run immediately: E.g. click to center
    """

    async def unrecognized_action(self, data, user_id):
        await self.conn_manager.broadcast(
            {
                Protocol.Key.STATUS_MSG: f"{user_id} sent unrecognized action {data}",
                Protocol.Key.STATUS: Protocol.Status.FAILURE,
            }
        )

    async def go_to_fiducial(self, data, user_id):
        start_bs.RE(
            start_bs.chip_scanner.drive_to_fiducial(
                data[Protocol.Key.METADATA][Protocol.Key.NAME]
            )
        )
        await self.conn_manager.broadcast(
            {
                Protocol.Key.STATUS_MSG: f"{user_id} moved to fiducial {data[Protocol.Key.METADATA]}",
                Protocol.Key.STATUS: Protocol.Status.SUCCESS,
            }
        )

    async def nudge_gonio(self, data: Dict[str, Any], user_id: str):
        start_bs.RE(
            start_bs.chip_scanner.nudge_by(
                data[Protocol.Key.METADATA][Protocol.Key.X_DELTA],
                data[Protocol.Key.METADATA][Protocol.Key.Y_DELTA],
            )
        )
        await self.conn_manager.broadcast(
            {
                Protocol.Key.STATUS_MSG: f"{user_id} moved gonio by {data[Protocol.Key.METADATA]}",
                Protocol.Key.STATUS: Protocol.Status.SUCCESS,
            }
        )

    async def set_fiducial(self, data: Dict[str, Any], user_id: str):
        start_bs.chip_scanner.manual_set_fiducial(
            data[Protocol.Key.METADATA]["fiducial_name"]
        )
        x_pos = start_bs.chip_scanner.x.get().user_readback
        y_pos = start_bs.chip_scanner.y.get().user_readback
        await self.conn_manager.broadcast(
            {
                Protocol.Key.STATUS_MSG: f"{user_id} set fiducial {data[Protocol.Key.METADATA]}: ({x_pos}, {y_pos})",
                Protocol.Key.STATUS: Protocol.Status.SUCCESS,
            }
        )

    async def move_gonio(self, data: Dict[str, Any], user_id: str):
        start_bs.RE(
            start_bs.chip_scanner.drive_to_position(
                data[Protocol.Key.METADATA][Protocol.Key.X_POS],
                data[Protocol.Key.METADATA][Protocol.Key.Y_POS],
            )
        )
        await self.conn_manager.broadcast(
            {
                Protocol.Key.STATUS_MSG: f"{user_id} moved gonio to {data[Protocol.Key.METADATA]}",
                Protocol.Key.STATUS: Protocol.Status.SUCCESS,
            }
        )

    async def add_to_queue(self, data: Dict[str, Any], user_id: str):
        """
        Adds request to queue, then broadcasts to all clients that a request has been added
        """

        self.request_queue.put(data[Protocol.Key.METADATA])
        await self.conn_manager.broadcast(
            {
                Protocol.Key.ACTION: Protocol.Action.ADD_TO_QUEUE,
                Protocol.Key.METADATA: {
                    Protocol.Key.USER: user_id,
                    Protocol.Key.REQUEST: data[Protocol.Key.METADATA],
                },
                Protocol.Key.STATUS_MSG: f"{user_id} added request {data[Protocol.Key.METADATA]}",
                Protocol.Key.STATUS: Protocol.Status.SUCCESS,
            }
        )

    async def collect_queue(self, data: Dict[str, Any], user_id: str):
        """
        Runs all tasks in the queue. Ideally will be excuted by the BlueSky run engine
        """
        while not self.request_queue.empty():
            item = self.request_queue.get()
            print(f"Working on : {item}")
            if len(item["address"]) == 3:
                print(f"Moving to {item['address']}")
                start_bs.RE(
                    start_bs.chip_scanner.drive_to_location(item["address"] + "a")
                )
            print(f"Completed : {item}")
            await self.conn_manager.broadcast(
                {
                    Protocol.Key.STATUS_MSG: f"Collecting request {item}",
                    Protocol.Key.STATUS: Protocol.Status.SUCCESS,
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
                Protocol.Key.STATUS_MSG: f"{user_id} cleared queue",
                Protocol.Key.ACTION: Protocol.Action.CLEAR_QUEUE,
                Protocol.Key.METADATA: {Protocol.Key.USER: user_id},
            }
        )

    async def send_login_result(self, success: bool, username: str, client_id: str):
        if success:
            data = {
                Protocol.Key.LOGIN: Protocol.Status.SUCCESS,
                Protocol.Key.STATUS_MSG: f"Successfully logged in as {username}",
            }
        else:
            data = {Protocol.Key.LOGIN: Protocol.Status.FAILURE}
        await self.conn_manager.unicast(data, client_id)
