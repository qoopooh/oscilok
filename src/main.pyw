#!/usr/bin/env python
"""Main Window
"""
import gc
import sys
#from pprint import pprint
import tkinter as tk
from tkinter import ttk

import usb

import readsample
import waveform


VERSION = "0.1.0"

POLLING_TIME = 500
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

    def toggle(self):
        """Toggle reading"""

        if self.polling:
            self.polling = False
            ng_status.config(text="-", background="")
            start_button.config(text="Start")

            print("gc.get_objects: {}".format(len(gc.get_objects())))
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
            self._data = []
            for channel in [readsample.CH1, readsample.CH2]:
                data = readsample.read(channel, verbose=False)
                if len(data) < 3000:
                    ch_label[channel-1].config(text="ch{}: -".format(channel))
                    device_status.config(text="No CH{}".format(channel))
                    self._inprogress()
                    return
                print('CH{} {} {} {}'.format(channel,
                    len(data), data[0], data[int(len(data) / 2)]))
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
            print(err)
            try:
                tk.messagebox.showerror("Device Error", "Please open the program again")
            except:
                pass
            sys.exit()

        if self._data[0] == self._data[1]:
            #tk.messagebox.showerror("Data conflict", "Please re-open the program")
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
            1: self._ng,
            2: self._check_wave,
        }
        signal_map[count]()


    def _check_wave(self) -> None:
        """Analyze wave form"""

        waves = []
        for idx, dat in enumerate(self._data):
            # Show wave form info on screen
            wave = waveform.get_wave_form(dat)
            ch_label[idx].config(text="ch{}: {} / {}".format(
                idx+1, wave.typ, len(wave.data)))
            waves.append(wave)

        sine, square = None, None
        for wave in waves:
            if wave.typ == waveform.WaveType.UNKNOWN:
                # unknown wave form, get sample again
                self._inprogress()
                return

            if wave.typ == waveform.WaveType.SINE:
                sine = wave.data
            elif wave.typ == waveform.WaveType.SQUARE:
                square = wave.data

        if waveform.is_top_sine_inside_top_square(sine, square):
            # Good result
            ng_status.config(text="OK", background=BG_OK)
        else:
            ng_status.config(text="NG", background=BG_NG)
        ng_status.after(POLLING_TIME, self.reading)


    def _inprogress(self) -> None:
        # query new data
        self._progress_idx += 1
        if self._progress_idx >= len(IN_PROGRESS_TEXT):
            self._progress_idx = 0

        ng_status.config(text=IN_PROGRESS_TEXT[self._progress_idx], background=BG_PROGRESS)
        ng_status.after(POLLING_TIME, self.reading)


    def _ng(self) -> None:
        # Failed result
        ng_status.config(text="NG", background=BG_NG)
        ng_status.after(POLLING_TIME, self.reading)


ctrl = Controller()

root = tk.Tk()
root.title("Oscilok V{}".format(VERSION))
root.minsize(300, 280)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

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
#label.pack()
    label.grid(row=index, column=0, sticky=tk.W)
    ch_label.append(label)

start_button = ttk.Button(root,
        text="Start",
        command=ctrl.toggle)
#start_button.pack()
start_button.grid(row=2, column=0, padx=20, pady=5,
        sticky=tk.N+tk.S+tk.W+tk.E)

device_status = ttk.Label(root, text=VERSION)
#device_status.pack(side=tk.BOTTOM)
device_status.grid(row=3, column=0, padx=10, pady=5, sticky=tk.N+tk.S+tk.W+tk.E)

root.mainloop()
