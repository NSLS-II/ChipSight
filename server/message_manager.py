from queue import Queue
from typing import Any, Callable, Dict, Optional, Type, TypeVar
from uuid import UUID

from model.comm_protocol import (
    ClearQueue,
    CollectNeighborhood,
    CollectQueue,
    CollectRow,
    ErrorResponse,
    ExecuteActionResponse,
    ExecuteRequest,
    GoToFiducial,
    LoginResponse,
    Message,
    MetadataType,
    MoveGonio,
    NudgeGonio,
    PayloadType,
    QueueActionResponse,
    QueueRequest,
    SetFiducial,
)
from server import start_bs

from .manager import ConnectionManager

T = TypeVar("T", bound=PayloadType)


class ChipScannerMessageManager:
    def __init__(self, connection_manager: ConnectionManager):
        self.name = "Chip scanner manager"
        self.conn_manager = connection_manager
        self.request_queue: Queue[PayloadType] = Queue()
        self.valid_queue_requests: Dict[Type[PayloadType], Callable] = {
            CollectNeighborhood: self.collect_neighborhood,
            CollectRow: self.collect_row,
        }
        self.valid_immediate_requests: Dict[Type[PayloadType], Callable] = {
            GoToFiducial: self.go_to_fiducial,
            ClearQueue: self.clear_queue,
        }

    async def process_message(self, data: Message, user_id: str):
        if isinstance(data.metadata, QueueRequest):
            await self.handle_queue_request(data.metadata, data.payload)
        elif isinstance(data.metadata, ExecuteRequest):
            await self.handle_execute_request(data.metadata, data.payload)

    async def handle_queue_request(
        self, metadata: QueueRequest, payload: Optional[PayloadType]
    ):
        if payload and type(payload) in self.valid_queue_requests:
            self.request_queue.put(payload)
            await self.conn_manager.broadcast(
                Message(
                    metadata=QueueActionResponse(
                        status_msg=f"{metadata.user_id} added request {str(payload)} to queue",
                        user_id=metadata.user_id,
                    ),
                    payload=payload,
                )
            )
        else:
            await self.conn_manager.unicast(
                Message(
                    metadata=ErrorResponse(
                        user_id=None,
                        status_msg="Could not find request in list of valid requests",
                    ),
                    payload=None,
                ),
                client_id=metadata.client_id,
            )

    """
    Other unimplemented commands:
     - Pause queue: Should complete current task and pause
     - Stop queue: Stop current task immediately 
     """

    async def handle_execute_request(
        self, metadata: ExecuteRequest, payload: Optional[PayloadType]
    ):
        if payload and type(payload) in self.valid_immediate_requests:
            run_engine_state = start_bs.RE.state
            if run_engine_state == "idle":
                self.valid_immediate_requests[type(payload)](
                    ExecuteActionResponse(), payload
                )
            elif run_engine_state == "running":
                await self.conn_manager.unicast(
                    Message(
                        metadata=ErrorResponse(
                            status_msg="Run engine is busy, cannot fulfill request"
                        )
                    ),
                    client_id=metadata.client_id,
                )
            elif run_engine_state == "paused":
                await self.conn_manager.unicast(
                    Message(
                        metadata=ErrorResponse(
                            status_msg="Run engine is paused, cannot fulfill request"
                        )
                    ),
                    client_id=metadata.client_id,
                )

    async def go_to_fiducial(
        self, response_metadata: MetadataType, payload: GoToFiducial
    ):
        start_bs.RE(start_bs.chip_scanner.drive_to_fiducial(payload.name))
        await self.conn_manager.broadcast(
            Message(metadata=response_metadata, payload=payload)
        )

    async def nudge_gonio(self, response_metadata: MetadataType, payload: NudgeGonio):
        start_bs.RE(
            start_bs.chip_scanner.nudge_by(
                payload.x_delta,
                payload.y_delta,
            )
        )
        await self.conn_manager.broadcast(
            Message(metadata=response_metadata, payload=payload)
        )

    async def set_fiducial(self, response_metadata: MetadataType, payload: SetFiducial):
        start_bs.chip_scanner.manual_set_fiducial(payload.name)
        await self.conn_manager.broadcast(
            Message(metadata=response_metadata, payload=payload)
        )

    async def move_gonio(self, response_metadata: MetadataType, payload: MoveGonio):
        start_bs.RE(
            start_bs.chip_scanner.drive_to_position(
                payload.x_pos,
                payload.y_pos,
            )
        )
        await self.conn_manager.broadcast(
            Message(metadata=response_metadata, payload=payload)
        )

    async def collect_neighborhood(
        self, response_metadata: MetadataType, payload: CollectNeighborhood
    ):
        start_bs.RE(
            start_bs.chip_scanner.ppmac_neighbourhood_scan(
                payload.location, payload.wait_time
            )
        )
        await self.conn_manager.broadcast(
            Message(metadata=response_metadata, payload=payload)
        )

    async def collect_row(self, response_metadata: MetadataType, payload: CollectRow):
        start_bs.RE(
            start_bs.chip_scanner.ppmac_single_line_scan(
                payload.location, payload.wait_time
            )
        )
        await self.conn_manager.broadcast(
            Message(metadata=response_metadata, payload=payload)
        )

    async def collect_queue(self, data: Dict[str, Any], user_id: str):
        """
        Runs all tasks in the queue. Ideally will be excuted by the BlueSky run engine
        """
        while not self.request_queue.empty():
            item = self.request_queue.get()
            print(f"Working on : {item}")
            await self.conn_manager.broadcast(
                Message(
                    metadata=QueueActionResponse(
                        status_msg=f"Collecting request {item}"
                    )
                )
            )
            response = QueueActionResponse()
            self.valid_queue_requests[type(item)](response, item)

            print(f"Completed : {item}")

            self.request_queue.task_done()

    async def clear_queue(self, data: Dict[str, Any], user_id: str):
        """
        Removes all pending tasks from the queue
        """
        with self.request_queue.mutex:
            self.request_queue.queue.clear()
        await self.conn_manager.broadcast(
            Message(metadata=ExecuteActionResponse(), payload=ClearQueue())
        )

    async def send_login_result(self, success: bool, username: str, client_id: UUID):
        if success:
            message = Message(
                metadata=LoginResponse(
                    status_msg=f"Successfully logged in as {username}",
                    login_success=True,
                )
            )
        else:
            message = Message(
                metadata=LoginResponse(
                    status_msg=f"Failed to log in as {username}", login_success=False
                )
            )
        await self.conn_manager.unicast(message=message, client_id=client_id)
