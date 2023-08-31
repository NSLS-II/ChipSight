from enum import Enum, EnumMeta
from dataclasses import dataclass
from typing import Literal


class Labels(Enum):
    ACTION = "action"
    METADATA = "metadata"
    USER = "user"
    REQUEST = "request"
    STATUS = "status"
    STATUS_MSG = "status_message"
    BROADCAST = "broadcast"
    ADDRESS = "address"


class Actions(Enum):
    ADD_TO_QUEUE = "add_to_queue"
    COLLECT_QUEUE = "collect_queue"
    CLEAR_QUEUE = "clear_queue"


class Status(Enum):
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class Protocol:
    Actions = Actions
    Status = Status
    Labels = Labels
