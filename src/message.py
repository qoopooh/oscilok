"""DSO Protocol Message"""

from array import array
from dataclasses import dataclass

DEBUG_MESSAGE_MARKER = 0x43
NORMAL_MESSAGE_MARKER = 0x53

SAMPLE_RESPONSE_CMD = 0x82
SAMPLE_LEN_SUBCMD   = 0x00
SAMPLE_DATA_SUBCMD  = 0x01
SAMPLE_SUM_SUBCMD   = 0x02
SAMPLE_STOP_SUBCMD  = 0x03 # Errors or STOP mode

NORMAL_SUBCOMMAND = [
    0x02, # Read sample data
    SAMPLE_RESPONSE_CMD,
    0x10, # Read file
    0x90,
    0x12, # Lock/unlock control panel, start/stop acquisition
    0x92,
    0xA0, # screenshot response
] # The command with subcommand

@dataclass
class Message:
    """Protocol Message"""

    mark: int = NORMAL_MESSAGE_MARKER
    length: int = 0
    command: int = 0
    subcommand: int = -1
    data: array = None
    checksum: bool = False
    response: bool = False # response from DSO


def build(pkt: array) -> Message:
    """Build a message from array"""

    if pkt[0] == 0:
        return None

    msg = Message(
            pkt[0],
            pkt[1] + (pkt[2] << 8),
            pkt[3])

    msg.checksum = _checksum(pkt)
    msg.response = msg.command >> 7 > 0

    if msg.length < 3:
        # no data, subcommand
        return msg

    data_idx = 4

    if msg.command in NORMAL_SUBCOMMAND:
        msg.subcommand = pkt[data_idx]
        data_idx += 1

    msg.data = pkt[data_idx: msg.length+2]

    return msg


def create_packet(msg: Message) -> array:
    """Create packet from a message"""

    pkt = array('B', [msg.mark, 0, 0, msg.command])
    length = 2

    if msg.subcommand > -1:
        pkt.append(msg.subcommand)
        length += 1
    if msg.data and len(msg.data) > 0:
        pkt.extend(msg.data)
        length += len(msg.data)

    pkt[1] = length & 0x00ff
    pkt[2] = length >> 8

    pkt.append(make_sum(pkt))

    return pkt


def make_sum(pkt: array) -> int:
    """Create check sum"""

    summary = 0
    for dat in pkt:
        summary += dat

    return summary & 0xFF


def _checksum(pkt: array) -> bool:

    pkt_len = pkt[1] + (pkt[2] << 8)
    chk_idx = pkt_len + 2
    if chk_idx >= len(pkt):
        return False

    return make_sum(pkt[:chk_idx]) == pkt[chk_idx]
