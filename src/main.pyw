#!/usr/bin/env python
"""Main Window
"""
import gc
import sys
import traceback
from datetime import datetime
from os import path, name
#from pprint import pprint
import tkinter as tk
from tkinter import ttk, messagebox # submodules

import usb

import dso
import log
import scope
import waveform
from waveform import WaveType


VERSION = "0.1.3"

MIN_VOLT_P2P = 2.5  # volts
POLLING_TIME = 500  # in millisecond
OK_SKIP_TIME = 2500 # in millisecond
BG_NG = 'red'
BG_OK = 'green'
BG_PROGRESS = 'white'
BG_LOSS = 'gray'
FONT = 'Arial'
IN_PROGRESS_TEXT = ('-', '\\', '|', '/')


class Controller:
    """GUI controller"""

    polling = False
    _data: list = []
    _progress_idx = 0
    _ng_count, _ok_count = 0, 0
    _print_time = None

    def toggle(self, _event=None):
        """Toggle reading"""

        if self.polling:
            self.polling = False
            ng_status.config(text="-", background="")
            start_button.config(text="Start")
            return

        self.polling = True
        start_button.config(text="Stop")
        ch_label[0].config(text='')
        ch_label[1].config(text='')
        device_status.config(text='')
        self.reading()


    def reading(self) -> None:
        """Reading data from Oscilloscope"""

        if not self.polling:
            return

        try:
            dev = scope.Scope(verbose=False)
            self._data = dev.dual()
            dev.close()

            for chan, wave in enumerate(self._data):
                if not wave.data:
                    ch_label[chan].config(text="ch{}: -".format(chan+1))
                    device_status.config(text="No CH{}".format(chan+1))
                    self._inprogress()
                    return

            device_status.config(text="")

        except scope.OscilloscopeNotFoundError as err:
            device_status.config(text=str(err))
            ng_status.config(text="-", background="")
            ng_status.after(POLLING_TIME + 2000, self.reading)
            return

        except dso.SampleLostError as err:
            device_status.config(text=str(err))
            ng_status.config(text="-", background="")
            ng_status.after(POLLING_TIME + 2000, self.reading)
            return

        except scope.OscilloscopeError as err:
            _logger.warning(err)
            device_status.config(text=str(err))
            ng_status.after(POLLING_TIME, self.reading)
            return

        except usb.core.USBTimeoutError as err:
            #
            # libusb0-dll:err [_usb_reap_async] timeout error
            #
            if dev:
                dev.close()
                dev = None
            _logger.warning(traceback.format_exc())

            device_status.config(text=str(err))
            ng_status.after(POLLING_TIME, self.reading)
            return

        except usb.core.USBError as err:
            _logger.error(err)
            try:
                messagebox.showerror("Device Error", "Please open the program again")
                sys.exit()
            except tk.TclError:
                pass
            raise err

        self._check_wave()


    def _check_wave(self) -> None:
        """Analyze wave form"""

        for idx, wave in enumerate(self._data):
            # Show wave form info on screen
            ch_label[idx].config(text="ch{}:{} ({}) Vp-p: {} V".format(
                idx+1, wave.typ, len(wave.data), wave.vpp))

        sine, square = None, None
        for wave in self._data:
            if wave.typ == WaveType.UNKNOWN:
                # unknown wave form, get sample again
                self._ng_count = 0
                self._ok_count = 0
                self._inprogress()
                return

            if wave.typ == WaveType.SINE:
                sine = wave.data

                if wave.vpp and wave.vpp < MIN_VOLT_P2P:
                    self._ng()
                    return

            elif wave.typ == WaveType.SQUARE:
                square = wave.data

        if not sine:
            self._inprogress()
            return

        if not waveform.is_top_sine_inside_top_square(sine, square):
            self._ng()
            return

        # Good result
        self._ok_count += 1
        self._ng_count = 0

        device_status.config(
            text="OK time: {} seconds".format(_polling_second_update(self._ok_count)))
        ng_status.config(text="OK", background=BG_OK)
        ng_status.after(POLLING_TIME, self.reading)

        if self._ok_count == 1:

            if name == 'nt':
                import winsound
                winsound.Beep(1000, 250)

            else:
                dev = dso.Dso()
                dev.buzzer(1)
                dev.read_message()
                dev.close()


    def _inprogress(self) -> None:
        """query new data"""
        self._progress_idx += 1
        if self._progress_idx >= len(IN_PROGRESS_TEXT):
            self._progress_idx = 0

        ng_status.config(text=IN_PROGRESS_TEXT[self._progress_idx], background=BG_PROGRESS)
        ng_status.after(POLLING_TIME, self.reading)


    def _ng(self) -> None:
        """Failed result"""
        self._ok_count = 0
        self._ng_count += 1

        device_status.config(
            text="NG time: {} seconds".format(_polling_second_update(self._ng_count)))
        ng_status.config(text="NG", background=BG_NG)
        ng_status.after(POLLING_TIME, self.reading)

        if self._ng_count == 2:

            if name == 'nt':
                import winsound
                winsound.Beep(2000, 1500)

            else:
                dev = dso.Dso()
                dev.buzzer(10)
                dev.read_message()
                dev.close()


def _polling_second_update(count: int) -> int:

    _print_total_seconds()
    out = count / (1000 / POLLING_TIME)
    return int(out)


def _print_total_seconds() -> None:

    delta = datetime.now() - start_time
    if delta.seconds % 60 == 0 and delta.microseconds < 500000:
        _logger.info("Running: %s -> %d", delta, len(gc.get_objects()))


ctrl = Controller()
_logger = log.setup_log('main')

root = tk.Tk()
root.title("Oscilok v{}".format(VERSION))
root.minsize(300, 280)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
if __file__.endswith("main.pyw"):
    # It will not show icon when you build it to single file
    img = tk.Image('photo', file=path.join(path.dirname(__file__), '..', 'img', 'oscilok_logo.png'))
    root.tk.call('wm', 'iconphoto', root._w, img)

ng_status = ttk.Label(root,
        text="-",
        font=(FONT, 72),
        width=7,
        anchor="center")
ng_status.grid(row=0, column=0, padx=10, pady=10,
        sticky=tk.E+tk.W+tk.N+tk.S)

frame = tk.Frame(root)
frame.grid(row=1, column=0, padx=10,
        sticky=tk.N+tk.S+tk.W+tk.E)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
ch_label = []
for index in range(2):
    label = ttk.Label(frame,
            font=(FONT, 8),
            text="ch{}: -".format(index + 1))
    label.grid(row=index, column=0, sticky=tk.W)
    ch_label.append(label)

start_button = ttk.Button(root,
        text="Start",
        command=ctrl.toggle)
start_button.grid(row=2, column=0, padx=20, pady=5,
        sticky=tk.N+tk.S+tk.W+tk.E)
start_button.focus_set()
root.bind("<Control-s>", ctrl.toggle)

device_status = ttk.Label(root, text="Version {}".format(VERSION))
device_status.grid(row=3, column=0, padx=10, pady=5, sticky=tk.N+tk.S+tk.W+tk.E)

start_time = datetime.now()
root.mainloop()
