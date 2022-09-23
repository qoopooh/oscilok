#!/usr/bin/env python
"""Main Window
"""
from os import path

import tkinter as tk
from tkinter import ttk  # submodules
from pynput import keyboard

import controller
from ng_state import NgState


VERSION = "0.1.6"

BG_NG = 'red'
BG_OK = 'green'
BG_PROGRESS = 'white'
IN_PROGRESS_TEXT = ('-', '\\', '|', '/')
FONT = 'Arial'


def _get_title() -> str:

    title = "Oscilok v{}".format(VERSION)
    if __file__.endswith('main.pyw'):
        title = "{} (main.pyw)".format(title)

    return title


def disable_buttons(disable: bool) -> None:
    """Disable all buttons"""

    state = tk.DISABLED if disable else tk.NORMAL

    start_button['state'] = state
    single_button['state'] = state


def set_reading_text(text) -> None:
    """Set Start / Stop status"""

    start_button.config(text=text)


def set_device_status(text) -> None:
    """Set device status"""

    device_status.config(text=text)


def set_channel_states(states) -> None:
    """Set channel status"""

    for chan, text in enumerate(states):
        if text == '-':
            text = 'ch{}: -'.format(chan + 1)
        ch_label[chan].config(text=text)


def set_ng_status(state: NgState) -> ttk.Label:
    """Set NG status"""

    funtions = {
        NgState.STOP: _ng_stop,
        NgState.PROGRESS: _ng_progress,
        NgState.NG: _ng_ng,
        NgState.OK: _ng_ok,
    }
    funtions[state]()
    return ng_status


def _ng_stop():

    ng_status.config(text="-", background="")


def _ng_progress():

    current_text = ng_status['text']
    if current_text in IN_PROGRESS_TEXT:
        idx = IN_PROGRESS_TEXT.index(current_text)
        idx += 1
        if idx >= len(IN_PROGRESS_TEXT):
            idx = 0
    else:
        idx = 0

    text = IN_PROGRESS_TEXT[idx]
    ng_status.config(text=text, background=BG_PROGRESS)


def _ng_ng():

    ng_status.config(text="NG", background=BG_NG)


def _ng_ok():

    ng_status.config(text="OK", background=BG_OK)


def on_press(key):
    """Listen keyboard pressed"""

    if key == keyboard.Key.media_volume_up:
        ctrl.single()
    else:
        print('on_press {}'.format(key))


listener = keyboard.Listener(
        on_press=on_press,
        on_release=None)
listener.start()


ctrl = controller.Controller()
ctrl.set_callbacks({
    "ng": set_ng_status,
    "reading": set_reading_text,
    "device": set_device_status,
    "channels": set_channel_states,
    "disable_buttons": disable_buttons,
})

root = tk.Tk()
root.title(_get_title())
root.minsize(300, 280)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
base_path = path.dirname(__file__)
if __file__.endswith("main.pyw"):
    img_path = path.join(base_path, '..', 'img', 'oscilok_logo.png')
else:
    # build file
    img_path = path.join(base_path, 'img', 'oscilok_logo.png')
img = tk.Image('photo', file=img_path)
root.tk.call('wm', 'iconphoto', root._w, img)

ng_status = ttk.Label(root, text="-",
                      font=(FONT, 72), width=7, anchor="center")
ng_status.grid(row=0, column=0, padx=10, pady=10, sticky=tk.E+tk.W+tk.N+tk.S)

frame = tk.Frame(root)
frame.grid(row=1, column=0, padx=10, sticky=tk.N+tk.S+tk.W+tk.E)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
ch_label = []
for index in range(2):
    label = ttk.Label(frame, font=(FONT, 8), text="ch{}: -".format(index + 1))
    label.grid(row=index, column=0, sticky=tk.W)
    ch_label.append(label)

start_button = ttk.Button(root, text="Start", command=ctrl.toggle)
start_button.grid(row=2, column=0, padx=20, pady=5,
                  sticky=tk.N+tk.S+tk.W+tk.E)
# start_button.focus_set()
# root.bind("<Control-s>", ctrl.toggle)
root.bind("<Return>", (lambda event: ctrl.single()))

single_button = ttk.Button(root, text="Single Read", command=ctrl.single)
single_button.grid(row=3, column=0, padx=20, pady=5,
                   sticky=tk.N+tk.S+tk.W+tk.E)
single_button.focus_set()

device_status = ttk.Label(root, text="Version {}".format(VERSION))
device_status.grid(row=4, column=0, padx=10, pady=5,
                   sticky=tk.N+tk.S+tk.W+tk.E)

root.mainloop()
