#!/usr/bin/env python
"""0x02 Read sample data
"""

import argparse
from array import array
from datetime import datetime, timedelta

import usb

import dso
import waveform

CH1 = 0x01
CH2 = 0x02
CACHE_MIN_LEN = 3200
CACHE_TIME_SECS = 3.5
CACHE_RECENT_SECS = 1.8

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-c', '--channel', type=int,
    help='Reading channel (1 - CH1, 2 - CH2)',
    default=CH1,
    choices=[CH1, CH2])
PARSER.add_argument('-d', '--dual', help='Dual channels', action='store_true')
PARSER.add_argument('-v', '--verbose', help='verbose', action='store_true')


class OscilloscopeNotFoundError(Exception):
    """Device Not Found"""

class OscilloscopeError(Exception):
    """Some thing wrong with device"""
    channel: int = None


class Cache:
    """Cache output data from Oscilloscope"""

    _buf = {
        0: {"data": None, "time": None},
        1: {"data": None, "time": None},
    }

    def __init__(self, verbose=False) -> None:
        self._verbose = verbose

    def set_cache(self, chan, data) -> None:
        """Save data to cache"""

        data_len = len(data)
        if data_len < CACHE_MIN_LEN:
            return

        if self._verbose:
            print('set_cache', chan, len(data))

        out = array('B')
        out.extend(data)

        self._buf[chan] = {
            "data": out,
            "time": datetime.now(),
        }


    def get_recent_cache(self, chan: int) -> array:
        """Has cache recently"""

        data = self._get_data_from_cache(chan, CACHE_RECENT_SECS)
        if len(data) > 0 and self._verbose:
            print('get_recent_cache {}: {}'.format(chan, len(data)))

        return data


    def get_cache(self, chan: int) -> array:
        """Get data from cache"""

        data = self._get_data_from_cache(chan, CACHE_TIME_SECS)
        if len(data) > 0 and self._verbose:
            print('get_cache {}: {}'.format(chan, len(data)))

        return data


    def _get_data_from_cache(self, chan: int, secs: int) -> array:

        if chan < 0 or chan >= len(self._buf):
            return array('B')

        data = self._buf[chan]["data"]
        timestamp = self._buf[chan]["time"]

        if not data or not timestamp:
            return array('B')

        if datetime.now() - timestamp > timedelta(seconds=secs):
            return array('B')

        return data


CACHE = Cache(verbose=False)


def read(channel: int, verbose=False) -> array:
    """Read sample data"""

    chan = channel - 1
    data = CACHE.get_recent_cache(chan)
    if len(data) > 0:
        return data

    dev = dso.Dso(verbose)
    try:
        if not dev.is_available():
            raise OscilloscopeNotFoundError(dev.error)

        #0x02 Read sample data
        dev.sample(chan)
        dev.echo()
        data, chan = dev.get_sample()

        CACHE.set_cache(chan, data)

    except usb.core.USBError as err:
        raise OscilloscopeError(str(err)) from err

    except dso.SampleLostError as err:
        error = OscilloscopeError(str(err))
        if err.channel:
            error.channel = err.channel
        raise error from err

    finally:
        dev.close()

    return CACHE.get_cache(chan)


def _write_output(data: array, channel: int) -> None:

    if len(data) == 0:
        return

    with open("sample{}.dat".format(channel), "w", encoding="ascii") as outfile:
        for dat in data:
            outfile.write("{}\n".format(int(dat)))

    with open("sample_b{}.dat".format(channel), "wb") as outfile:
        outfile.write(data)


def _print_wave(data: array):

    wave = waveform.get_wave_form(data)
    for dot in wave.data:
        print(dot)

    print(wave.typ)


if __name__ == '__main__':

    ARGS = PARSER.parse_args()

    if ARGS.dual:

        DATA1 = read(CH1, ARGS.verbose)
        _write_output(DATA1, CH1)

        DATA2 = read(CH2, ARGS.verbose)
        _write_output(DATA2, CH2)

    else:

        DATA = read(ARGS.channel, ARGS.verbose)
        _write_output(DATA, ARGS.channel)

        if len(DATA) > 3000:
            _print_wave(DATA)
