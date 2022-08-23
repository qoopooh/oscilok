"""Oscilloscope Settings"""
from array import array
from enum import Enum


class VoltDIVx1(Enum):
    """VOLTS / DIV x1"""

    # Probe 1x
    MV2     = 0
    MV5     = 1
    MV10    = 2
    MV20    = 3
    MV50    = 4
    MV100   = 5
    MV200   = 6
    MV500   = 7
    V1      = 8
    V2      = 9
    V5      = 10
    # V10   = 11 # got 0 instead


class VoltDIVx10(Enum):
    """VOLTS / DIV x10"""

    # Probe 10x
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
    # V100  = 11 # got 0 instead


class VoltDIVx100(Enum):
    """VOLTS / DIV x100"""

    # Probe 100x
    MV200   = 0
    MV500   = 1
    V1      = 2
    V2      = 3
    V5      = 4
    V10     = 5
    V20     = 6
    V50     = 7
    V100    = 8


class VoltMULTIPLY(Enum):
    """VOLTS / DIV"""

    MV2     = 0.000114
    MV5     = 0.000286
    MV10    = 0.000572
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
    V100    = 4.66666


class SecDIV(Enum):
    """SEC / DIV"""

    NS2     = 0
    NS4     = 1
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
    CH1_PROBE   = 5     # Line 6
    CH2_VOLTDIV = 11    # Line 12
    CH2_PROBE   = 15    # Line 16
    SECDEV      = 156   # Line 156, 157 Window time base


PROBES = [VoltDIVx1, VoltDIVx10, VoltDIVx100]


def create(data: array) -> dict:
    """Create settings data from array"""

    out = {
        "raw": data,
        Settings.SECDEV.name: SecDIV(data[Settings.SECDEV.value]),
        Settings.CH1_PROBE.name: PROBES[data[Settings.CH1_PROBE.value]],
        Settings.CH2_PROBE.name: PROBES[data[Settings.CH2_PROBE.value]],
    }

    for channel in range(1, 3):

        voltdiv = 'CH{}_VOLTDIV'.format(channel)
        probe = 'CH{}_PROBE'.format(channel)

        val = out[probe](data[Settings[voltdiv].value])
        out[voltdiv] = val.name

    return out
