#!/usr/bin/env python
"""Main Window
"""
import gc
import sys
from datetime import datetime
from os import path
#from pprint import pprint
import tkinter as tk
from tkinter import ttk, messagebox # submodules

import usb

import dso
import readsample
import waveform


VERSION = "0.1.0"

POLLING_TIME = 500    # in millisecond
OK_SKIP_TIME = 2500   # in millisecond
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

        #if self._should_hold_the_ok_result():
            ## should remove this block when USB communication is more stable
            #ng_status.after(POLLING_TIME, self.reading)
            #return

        try:
            self._data = []
            for channel in [readsample.CH1, readsample.CH2]:
                data = readsample.read(channel, verbose=False)
                if len(data) < 3000:
                    ch_label[channel-1].config(text="ch{}: -".format(channel))
                    device_status.config(text="No CH{}".format(channel))
                    self._inprogress()
                    return
                #print('CH{} {} {} {}'.format(channel,
                    #len(data), data[0], data[int(len(data) / 2)]))
                self._data.append(data)
            device_status.config(text="")

        except readsample.OscilloscopeNotFoundError as err:
            device_status.config(text=str(err))
            ng_status.config(text="-", background="")
            ng_status.after(POLLING_TIME + 2000, self.reading)
            return

        except readsample.OscilloscopeError as err:
            device_status.config(text=str(err))
            ng_status.after(POLLING_TIME, self.reading)
            return

        except usb.core.USBError as err:
            print(datetime.now() - start_time, err)
            try:
                messagebox.showerror("Device Error", "Please open the program again")
                sys.exit()
            except tk.TclError:
                pass
            raise err

        if self._data[0] == self._data[1]:
            #messagebox.showerror("Data conflict", "Please re-open the program")
            #sys.exit()
            device_status.config(text="Data conflict")
            self._inprogress()
            return

        count = 0
        for idx, dat in enumerate(self._data):
            # Get a signal or just straight line
            signal = waveform.has_signal(dat[1000:2000])
            ch_label[idx].config(text="ch{}: {}".format(idx+1, signal))
            if signal:
                count += 1

        signal_map = {
            0: self._inprogress,
            #1: self._ng,
            1: self._check_wave,
            2: self._check_wave,
        }
        signal_map[count]()


    def _should_hold_the_ok_result(self) -> bool:
        """Keep OK result without new data from oscilloscope"""

        if self._ok_count < 1:
            return False

        available_period = int(OK_SKIP_TIME / POLLING_TIME)
        if self._ok_count % available_period != 0:
            self._ok_count += 1
            device_status.config(
                text="OK time: {} seconds".format(_polling_second_update(self._ok_count)))
            return True

        return False


    def _check_wave(self) -> None:
        """Analyze wave form"""

        waves = []
        for idx, dat in enumerate(self._data):
            # Show wave form info on screen
            wave = waveform.get_wave_form(dat)
            ch_label[idx].config(text="ch{}: {} / {}".format(
                idx+1, wave.typ, len(wave.data)))
            waves.append(wave)

        if waves[0].typ == waves[1].typ:
            # same shape
            device_status.config(text="Same wave type")
            self._inprogress()
            return

        sine, square = None, None
        for wave in waves:
            if wave.typ == waveform.WaveType.UNKNOWN:
                # unknown wave form, get sample again
                self._ng_count = 0
                self._ok_count = 0
                self._inprogress()
                return

            if wave.typ == waveform.WaveType.SINE:
                sine = wave.data
            elif wave.typ == waveform.WaveType.SQUARE:
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
        if self._ng_count == 1:
            dev = dso.Dso()
            dev.buzzer(3)
            dev.close()

        device_status.config(
            text="NG time: {} seconds".format(_polling_second_update(self._ng_count)))
        ng_status.config(text="NG", background=BG_NG)
        ng_status.after(POLLING_TIME, self.reading)


def _polling_second_update(count: int) -> int:

    _print_total_seconds()
    out = count / (1000 / POLLING_TIME)
    return int(out)


def _print_total_seconds() -> None:

    delta = datetime.now() - start_time
    if delta.seconds % 15 == 0 and delta.microseconds < 500000:
        print("Running: {} -> {}".format(delta, len(gc.get_objects())))


ctrl = Controller()

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
