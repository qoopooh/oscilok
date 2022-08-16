"""Oscilloscope Settings"""
from array import array
from enum import Enum


class VoltDIV(Enum):
    """VOLTS / DIV"""

    MV20    = 0
    MV50    = 1
    MV100   = 2
    MV200   = 3
    MV500   = 4
    V1      = 5
    V2      = 6
    V5      = 7
    V10     = 8
    V20     = 9
    V50     = 10
    #V100    = 11 # got 0 instead


class VoltMULTIPLY(Enum):
    """VOLTS / DIV"""

    MV20    = 0.001144
    MV50    = 0.002288
    MV100   = 0.00444
    MV200   = 0.00926
    MV500   = 0.02389
    V1      = 0.04581
    V2      = 0.08918
    V5      = 0.25833
    V10     = 0.43306
    V20     = 0.87619
    V50     = 2.33333


class SecDIV(Enum):
    """SEC / DIV"""

    NS8     = 2
    NS20    = 3
    NS40    = 4
    NS80    = 5
    NS200   = 6
    NS400   = 7
    NS800   = 8
    US2     = 9
    US4     = 10
    US8     = 11
    US20    = 12
    US40    = 13
    US80    = 14
    US200   = 15
    US400   = 16
    US800   = 17
    MS2     = 18
    MS4     = 19
    MS8     = 20
    MS20    = 21
    MS40    = 22
    MS80    = 23
    MS200   = 24
    MS400   = 25


class Settings(Enum):
    """Concerned settings"""

    CH1_VOLTDIV = 1     # Line 2
    CH2_VOLTDIV = 11    # Line 12
    SECDEV = 156        # Line 156, 157


def create(data: array) -> dict:
    """Create settings data from array"""

    out = {
        "raw": data,
    }
    for member in Settings:
        if member == Settings.SECDEV:
            out[member.name] = SecDIV(data[member.value])
        else:
            out[member.name] = VoltDIV(data[member.value])

    return out
