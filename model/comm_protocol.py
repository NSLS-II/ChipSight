from dataclasses import dataclass


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


@dataclass(frozen=True)
class Action:
    ADD_TO_QUEUE = "add_to_queue"
    COLLECT_QUEUE = "collect_queue"
    CLEAR_QUEUE = "clear_queue"
    MOVE_GONIO = "move_gonio"
    NUDGE_GONIO = "nudge_gonio"
    SET_FIDUCIAL = "set_fiducial"


@dataclass(frozen=True)
class Status:
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class Protocol:
    Action = Action
    Status = Status
    Key = Key
