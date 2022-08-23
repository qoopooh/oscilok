"""Window Controller"""

import gc
import os
import sys
import threading
import traceback
from datetime import datetime

import tkinter as tk
from tkinter import messagebox  # submodules

import usb
import dso
import log
import scope
import waveform
from ng_state import NgState

if os.name == 'nt':
    import winsound


MIN_VOLT_P2P = 2.5      # volts
POLLING_TIME = 500      # in millisecond
SINGLE_READ_TRY_COUNT = 6


class Controller:
    """GUI controller"""

    polling = False
    _progress_idx = 0
    _ng_count, _ok_count = 0, 0
    _cb = None
    _single_read_try_count = 0
    _scope: scope.Scope = None

    def __init__(self):
        self._scope = scope.Scope(verbose=False)

    def set_callbacks(self, callbacks):
        """Set callbacks to GUI"""

        self._cb = callbacks

    def toggle(self, _event=None):
        """Toggle reading"""

        self._ok_count = 0
        self._ng_count = 0

        if self.polling:
            self.polling = False
            self._cb['ng'](NgState.STOP)
            self._cb['reading']("Start")
            self._scope.close()
            return

        self.polling = True
        self._cb['reading']("Stop")
        self._cb['channels'](['', ''])
        self._cb['device']('')
        self._reading()

    def single(self) -> None:
        """Single read"""

        self._single_read_try_count = SINGLE_READ_TRY_COUNT
        self._cb['disable_buttons'](True)

        if self.polling:
            return

        self.toggle()

    def _reading(self) -> None:
        """Reading data from Oscilloscope"""

        if not self.polling:
            return

        try:

            data = self._scope.dual()

            for chan, wave in enumerate(data):
                if not wave.data:
                    self._cb['channels'](['-', '-'])
                    self._cb['device']("No CH{}".format(chan+1))
                    self._inprogress()
                    return
            self._cb['device']('')

        except scope.OscilloscopeNotFoundError as err:
            self._cb['device'](err)
            self._cb['ng'](NgState.STOP).after(POLLING_TIME + 2000,
                                               self._reading)
            self._cb['disable_buttons'](False)

            self._clear_single_count()
            return

        except dso.SampleLostError as err:
            self._cb['device'](err)
            self._cb['ng'](NgState.STOP).after(POLLING_TIME + 2000,
                                               self._reading)
            return

        except scope.OscilloscopeError as err:
            _logger.warning(err)
            self._cb['device'](err)
            self._cb['ng'](NgState.STOP).after(POLLING_TIME, self._reading)

            self._clear_single_count()
            self._scope.close()
            return

        except usb.core.USBTimeoutError as err:
            #
            # libusb0-dll:err [_usb_reap_async] timeout error
            #
            _logger.warning(traceback.format_exc())

            self._cb['device'](err)
            self._cb['ng'](NgState.STOP).after(POLLING_TIME, self._reading)
            self._cb['disable_buttons'](False)

            self._clear_single_count()
            self._scope.close()
            return

        except usb.core.NoBackendError as err:
            _logger.error(err)
            messagebox.showerror("Device Error", err)
            sys.exit()

        except usb.core.USBError as err:
            _logger.error(traceback.format_exc())
            try:
                messagebox.showerror("Device Error", err)
            except tk.TclError as tkerr:
                _logger.error(tkerr)
            sys.exit()

        self._check_wave(data)

    def _check_wave(self, data: list) -> None:
        """Analyze wave form"""

        channels = []
        for idx, wave in enumerate(data):
            # Show wave form info on screen
            text = "ch{}:{} ({}) Vp-p: {} V".format(
                idx+1, wave.typ, len(wave.data), wave.vpp)
            channels.append(text)
        self._cb['channels'](channels)

        sine, square = None, None
        for wave in data:
            if wave.typ == waveform.WaveType.UNKNOWN:
                # unknown wave form, get sample again
                self._ng_count = 0
                self._ok_count = 0
                if self._single_read_count():
                    return
                self._inprogress()
                return

            if wave.typ == waveform.WaveType.SINE:
                sine = wave.data

                if wave.vpp and wave.vpp < MIN_VOLT_P2P:
                    self._ng()
                    self._cb['device']('Low voltage')
                    return

            elif wave.typ == waveform.WaveType.SQUARE:
                square = wave.data

        if not sine:
            if self._single_read_count():
                return
            self._inprogress()
            return

        if not waveform.is_top_sine_inside_top_square(sine, square):
            self._cb['device']('Not Sync')
            self._ng()
            return

        # Good result
        self._ok()

    def _clear_single_count(self) -> None:
        """Clear single count"""

        if self._single_read_try_count > 0:
            self.toggle()
        self._single_read_try_count = 0

    def _single_read_count(self) -> bool:
        """Return NG status"""

        if self._single_read_try_count > 0:
            self._single_read_try_count -= 1
            _logger.info("single_read: %d", self._single_read_try_count)
            if self._single_read_try_count == 1:
                self._ng()
                self._cb['device']('Cannot get sine wave')
                return True
        return False

    def _inprogress(self) -> None:
        """query new data"""
        self._cb['ng'](NgState.PROGRESS).after(POLLING_TIME, self._reading)

    def _ok(self) -> None:
        """OK result"""

        self._ok_count += 1
        self._ng_count = 0

        if self._single_read_try_count > 0:
            self.toggle()
            self.beep(True)
            msg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._single_read_try_count = 0
        else:
            update_time = _polling_second_update(self._ok_count)
            msg = "OK time: {} seconds".format(update_time)

        self._cb['device'](msg)
        self._cb['ng'](NgState.OK).after(POLLING_TIME, self._reading)
        self._cb['disable_buttons'](False)

        if self._ok_count == 1:
            self.beep(True)

    def _ng(self) -> None:
        """Failed result"""

        self._ok_count = 0
        self._ng_count += 1

        if self._single_read_try_count > 0:
            self.toggle()
            self.beep(False)
            self._single_read_try_count = 0
        else:
            cnt = _polling_second_update(self._ng_count)
            self._cb['device']("NG time: {} seconds".format(cnt))
        self._cb['ng'](NgState.NG).after(POLLING_TIME, self._reading)
        self._cb['disable_buttons'](False)

        if self._ng_count == 1:

            self.beep(False)

    def beep(self, result_ok=True) -> None:
        """Create beep sound"""

        if os.name == 'nt':
            threading.Thread(target=_beep_thread, args=(result_ok,)).start()
            return

        delay = 1 if result_ok else 10
        self._scope.alarm(delay)


def _beep_thread(result_ok: bool) -> None:
    """Windows beep thread"""

    if result_ok:
        winsound.Beep(1000, 250)
    else:
        winsound.Beep(2000, 1500)


def _polling_second_update(count: int) -> int:

    _print_total_seconds()
    out = count / (1000 / POLLING_TIME)
    return int(out)


def _print_total_seconds() -> None:

    delta = datetime.now() - start_time
    if delta.seconds % 60 == 0 and delta.microseconds < 500000:
        # randomly show log
        _logger.info("Running: %s -> %s",
                     delta, gc.get_count())
        # gc.collect()


start_time = datetime.now()
_logger = log.setup_log('ctrl')
