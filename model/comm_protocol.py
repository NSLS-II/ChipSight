from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel

# =============================================================================
# Section 1: Message Types
# =============================================================================


class Metadata(BaseModel):
    user_id: Optional[str] = None
    timestamp: datetime = datetime.now()
    message_type: str


class QueueRequest(Metadata):
    client_id: UUID
    message_type: Literal["queue_request"] = "queue_request"


class ExecuteRequest(Metadata):
    client_id: UUID
    message_type: Literal["execute_request"] = "execute_request"


class QueueActionResponse(Metadata):
    message_type: Literal["queue_response"] = "queue_response"
    status_msg: str = ""


class ExecuteActionResponse(Metadata):
    message_type: Literal["execute_response"] = "execute_response"


class ErrorResponse(Metadata):
    message_type: Literal["error"] = "error"
    status_msg: str = ""


class LoginResponse(Metadata):
    message_type: Literal["login"] = "login"
    status_msg: str = ""
    login_success: bool


MetadataType = Union[
    QueueRequest,
    ExecuteRequest,
    QueueActionResponse,
    ErrorResponse,
    ExecuteActionResponse,
    LoginResponse,
]


class Payload(BaseModel):
    payload_type: str


class NudgeGonio(Payload):
    payload_type: Literal["nudge_gonio"] = "nudge_gonio"
    x_delta: float
    y_delta: float
    z_delta: float


class MoveGonio(Payload):
    payload_type: Literal["move_gonio"] = "move_gonio"
    x_pos: float
    y_pos: float
    z_pos: float


class SetFiducial(Payload):
    payload_type: Literal["set_fiducial"] = "set_fiducial"
    name: str


class GoToFiducial(Payload):
    payload_type: Literal["go_to_fiducial"] = "go_to_fiducial"
    name: str


class CollectNeighborhood(Payload):
    payload_type: Literal["collect_neighborhood"] = "collect_neighborhood"
    location: str
    wait_time: int

    def __str__(self):
        return f"collect neighborhood {self.location}"


class CollectRow(Payload):
    payload_type: Literal["collect_line"] = "collect_line"
    location: str
    wait_time: int

    def __str__(self):
        return f"collect row {self.location}"


class CollectQueue(Payload):
    payload_type: Literal["collect_queue"] = "collect_queue"


class ClearQueue(Payload):
    payload_type: Literal["clear_queue"] = "clear_queue"


class RemoveFromQueue(Payload):
    payload_type: Literal["remove_from_queue"] = "remove_from_queue"
    index: int


PayloadType = Union[
    NudgeGonio,
    MoveGonio,
    SetFiducial,
    GoToFiducial,
    CollectNeighborhood,
    CollectRow,
    ClearQueue,
    CollectQueue,
    RemoveFromQueue,
]


class Message(BaseModel):
    metadata: MetadataType
    payload: Optional[PayloadType] = None


"""
@dataclass(frozen=True)
class Key:
    ACTION = "action"
    METADATA = "metadata"
    USER = "user"
    REQUEST = "request"
    STATUS = "status"
    STATUS_MSG = "status_message"
    BROADCAST = "broadcast"
    UNICAST = "unicast"
    ADDRESS = "address"
    MOVE_GONIO = "move_gonio"
    LOGIN = "login"
    ERROR = "error"
    NAME = "name"
    X_POS = "x_position"
    Y_POS = "y_position"
    Z_POS = "z_position"
    X_DELTA = "x_delta"
    Y_DELTA = "y_delta"
    Z_DELTA = "z_delta"



@dataclass(frozen=True)
class Action:
    ADD_TO_QUEUE = "add_to_queue"
    COLLECT_QUEUE = "collect_queue"
    CLEAR_QUEUE = "clear_queue"
    MOVE_GONIO = "move_gonio"
    NUDGE_GONIO = "nudge_gonio"
    SET_FIDUCIAL = "set_fiducial"
    GO_TO_FIDUCIAL = "go_to_fiducial"


@dataclass(frozen=True)
class Status:
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class Protocol:
    Action = Action
    Status = Status
    Key = Key

"""
