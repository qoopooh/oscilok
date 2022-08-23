"""NG status"""

from enum import Enum, auto


class NgState(Enum):
    """NG screen status"""

    STOP = auto()
    PROGRESS = auto()
    NG = auto()
    OK = auto()
