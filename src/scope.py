#!/usr/bin/env python
"""0x02 Read sample data
"""

import argparse
import time
from array import array
from datetime import datetime
from pprint import pprint

#import usb

import dso
import log
import settings
import waveform

CH1 = 0x01
CH2 = 0x02

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-a', '--alarm', help='alarm with buzzer', action='store_true')
PARSER.add_argument('-c', '--channel', type=int,
    help='Read a channel (1 - CH1, 2 - CH2)',
    default=CH1,
    choices=[CH1, CH2])
PARSER.add_argument('-d', '--dual', help='Read both channels', action='store_true')
PARSER.add_argument('-s', '--settings', help='Get settings', action='store_true')
PARSER.add_argument('-v', '--verbose', help='verbose', action='store_true')


class OscilloscopeNotFoundError(Exception):
    """Device Not Found"""

class OscilloscopeError(Exception):
    """Some thing wrong with device"""
    channel: int = None


class Scope:
    """Oscilloscope"""

    _dso: dso.Dso = None
    _settings: settings.Settings = None

    def __init__(self, verbose=False) -> None:
        self._verbose = verbose
        self._dso = dso.Dso(verbose)


    def alarm(self) -> None:
        """Alarm with buzzer"""

        dev = self._get_dev()
        dev.buzzer(1)
        msg = dev.read_message()
        if self._verbose:
            print(msg)


    def dual(self) -> list: # waveform.Wave
        """Read dual channel"""

        out = []
        for chan in range(2):
            data = self.read(chan + 1)
            out.append(data)

        return out


    def read(self, channel: int) -> waveform.Wave:
        """Read a single channel"""

        dev = self._get_dev()

        if not self._settings:
            self.dso_settings()
        time.sleep(.1)

        chan = channel - 1
        dev.sample(chan)
        data, resp = dev.get_sample()
        if resp != chan:
            _logger.warning("wrong chan %d -> %d", chan, resp)
            data, resp = dev.get_sample()
            if resp != chan:
                _logger.warning("wrong chan again %d -> %d", chan, resp)

        wave = waveform.get_wave_form(data)
        chx_key = 'CH{}_VOLTDIV'.format(channel)
        if self._settings \
            and chx_key in self._settings \
            and resp == chan:
            vdiv = self._settings[chx_key]
            wave.vpp = wave.p2p * settings.VoltMULTIPLY[vdiv.name].value

        return wave


    def dso_settings(self) -> dict:
        """Read DSO settings
        - TIME/DIV
        - VOLT/DIV (CH1, CH2)"""

        dev = self._get_dev()

        # dev.lock_panel(True)
        # msg = dev.read_message()
        # print(msg)
        # if msg.command != 0x92:
        #     _logger.warning("Wrong lock resp: {}".format(msg))

        dev.read_settings()
        data = dev.get_settings()
        if len(data) != 213:
            return None

        sett = settings.create(data)
        self._settings = sett.copy()
        del self._settings['raw']

        # time.sleep(.1)
        # dev.lock_panel(False)
        # msg = dev.read_message(10)
        # if not msg or msg.command != 0x92:
        #     _logger.warning("Wrong unlock resp: {}".format(msg))

        return sett

    def close(self) -> None:
        """Close device"""

        if self._dso:
            self._dso.close()
            self._dso = None


    def _get_dev(self):
        """Get DSO instance"""

        if not self._dso:
            self._dso = dso.Dso(self._verbose)

        if not self._dso.is_available():
            _logger.info('OscilloscopeNotFoundError')
            raise OscilloscopeNotFoundError(self._dso.error)

        return self._dso


def _save_settings(data: array) -> None:
    """Save scope settings"""

    now = datetime.now()
    filename = "settings-{}.dat".format(now.strftime("%Y%m%d%H%M%S"))
    with open(filename, 'w', encoding='ascii') as outfile:
        outfile.writelines(["{}\n".format(dat) for dat in data])


if __name__ == '__main__':

    ARGS = PARSER.parse_args()

    DEV = Scope(ARGS.verbose)

    if ARGS.dual:
        OUT = DEV.dual()
        for CHANNEL in OUT:
            pprint(CHANNEL)

    elif ARGS.alarm:
        DEV.alarm()

    elif ARGS.settings:
        OUT = DEV.dso_settings()
        _save_settings(OUT['raw'])
        print('dso_settings', OUT)

    else:
        OUT = DEV.read(ARGS.channel)
        print('channel', OUT)

    DEV.close()

_logger = log.setup_log('scope')
