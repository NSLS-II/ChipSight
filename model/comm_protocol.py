from dataclasses import dataclass


@dataclass(frozen=True)
class Labels:
    ACTION = "action"
    METADATA = "metadata"
    USER = "user"
    REQUEST = "request"
    STATUS = "status"
    STATUS_MSG = "status_message"
    BROADCAST = "broadcast"
    ADDRESS = "address"


@dataclass(frozen=True)
class Actions:
    ADD_TO_QUEUE = "add_to_queue"
    COLLECT_QUEUE = "collect_queue"
    CLEAR_QUEUE = "clear_queue"


@dataclass(frozen=True)
class Status:
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class Protocol:
    Actions = Actions
    Status = Status
    Labels = Labels
