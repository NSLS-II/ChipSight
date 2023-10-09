from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

# =============================================================================
# Section 1: Metadata
# =============================================================================


class Metadata(BaseModel):
    """
    A model representing metadata for communication messages.

    Attributes:
    -----------
    user_id : Optional[str]
        A unique identifier for the user, default is None.
    timestamp : datetime
        The time at which the message is created, default is the current time.
    message_type : str
        The type of the message being sent.
    """

    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    message_type: str


class QueueRequest(Metadata):
    """
    A metadata model that represents a request made by a client to
    add an action to the queue
    """

    client_id: UUID
    message_type: Literal["queue_request"] = "queue_request"


class ExecuteRequest(Metadata):
    """
    Metadata model to represent request made by a client to the server
    to execute an action immediately
    """

    client_id: UUID
    message_type: Literal["execute_request"] = "execute_request"


class QueueActionResponse(Metadata):
    """
    Response data sent by the server to the client that indicates whether
    an action is added to the queue
    """

    message_type: Literal["queue_response"] = "queue_response"
    status_msg: str = ""


class ExecuteActionResponse(Metadata):
    """
    Response data sent to client indicating if the immediate action was
    executed
    """

    message_type: Literal["execute_response"] = "execute_response"


class ErrorResponse(Metadata):
    """
    Response data sent to client to indicate errors
    """

    message_type: Literal["error"] = "error"
    status_msg: str = ""


class LoginResponse(Metadata):
    """
    Response data sent to client to indicate if login was successful
    """

    message_type: Literal["login"] = "login"
    status_msg: str = ""
    login_success: bool


class StatusResponse(Metadata):
    message_type: Literal["status"] = "status"
    status_msg: str = ""


MetadataType = Union[
    QueueRequest,
    ExecuteRequest,
    QueueActionResponse,
    ErrorResponse,
    ExecuteActionResponse,
    LoginResponse,
    StatusResponse,
]

# =============================================================================
# Section 2: Payload
# =============================================================================


class Payload(BaseModel):
    """
    Every message contains a payload that tells the receiver the
    information needed to complete a required task
    """

    payload_type: str


class NudgeGonio(Payload):
    """
    Payload to indicate the change in x, y, z directions to move the gonio

    """

    payload_type: Literal["nudge_gonio"] = "nudge_gonio"
    x_delta: float
    y_delta: float
    z_delta: float


class MoveGonio(Payload):
    """
    Payload to indicate the exact position to move the gonio to
    """

    payload_type: Literal["move_gonio"] = "move_gonio"
    x_pos: float
    y_pos: float
    z_pos: float


class SetFiducial(Payload):
    """
    Payload to indicate which fiducial the current gonio positions belong to
    name: str
        - Name of the fiducial to be set (e.g. F0, F1, F2)
    """

    payload_type: Literal["set_fiducial"] = "set_fiducial"
    name: str


class GoToFiducial(Payload):
    """
    Payload to indicate fiducial location to go to
    name: str
        - Name of the fiducial to go to (e.g. F0, F1, F2)

    Example:
    --------
    >>> GotoFiducial(name="F0")
    """

    payload_type: Literal["go_to_fiducial"] = "go_to_fiducial"
    name: str


class CollectNeighborhood(Payload):
    """
    Neighborhood to collect data from
    location: str
        - Two letter block name to collect data from (A1, B2 etc.)
    wait_time: int
        - Amount of time the sample is exposed in ms

    Example:
    --------
    >>> CollectNeighborhood(location="A1", wait_time=20)
    """

    payload_type: Literal["collect_neighborhood"] = "collect_neighborhood"
    location: str
    wait_time: int

    def __str__(self):
        return f"collect neighborhood {self.location}"


class CollectRow(Payload):
    """
    Payload to indicate the row to collect data from
    location: str
        - Three letter block name
    wait_time: int
        - Exposure time (ms)

    Example:
    --------
    >>> CollectRow(location="A1a", wait_time=20)
    """

    payload_type: Literal["collect_line"] = "collect_line"
    location: str
    wait_time: int

    def __str__(self):
        return f"collect row {self.location}"


class CollectQueue(Payload):
    """
    Collect queue, generally an immediate request
    """

    payload_type: Literal["collect_queue"] = "collect_queue"


class ClearQueue(Payload):
    """
    Clear the queue of all requests, generally an immediate request
    """

    payload_type: Literal["clear_queue"] = "clear_queue"


class RemoveFromQueue(Payload):
    """
    Remove specific index from queue, generally an immediate request
    """

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

# =============================================================================
# Section 3: Message
# =============================================================================


class Message(BaseModel):
    metadata: MetadataType
    payload: Optional[PayloadType] = None
