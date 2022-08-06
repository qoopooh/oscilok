#!/usr/bin/env python
"""DSO device
https://elinux.org/Das_Oszi_Protocol
"""

import argparse
import time
import warnings
from array import array
from datetime import datetime

import usb

import message


PARSER = argparse.ArgumentParser('DSO')
PARSER.add_argument('-b', '--buzzer', help='Buzzer n * 100ms', type=int)
PARSER.add_argument('-e', '--echo', help='echo command')
PARSER.add_argument('-I', '--init', help='Init DSO', action='store_true')
PARSER.add_argument('-l', '--lock', help='Lock panel', action='store_true')
PARSER.add_argument('-T', '--set_time', help='Set system time (now)', action='store_true')
PARSER.add_argument('-s', '--settings', help='Read settings', action='store_true')
PARSER.add_argument('-S', '--sample', help='Read sample from channel 1 or 2', type=int)
PARSER.add_argument('-u', '--unlock', help='Unlock panel', action='store_true')
PARSER.add_argument('-v', '--verbose', help='verbose', action='store_true')


class Dso:
    """Oscillator device (USB)"""

    error: str
    _interface = 0

    def __init__(self, verbose=False):

        self._verbose = verbose
        vendor = 0x049f
        product = 0x505a
        self._dev = usb.core.find(idVendor=vendor, idProduct=product)
        if not self._dev:
            self.error = 'Device Not Found'
            return

        cfg = self._dev.get_active_configuration()
        intf = cfg[(0, 0)]
        self._outbound = intf[1]  # 0x81
        self._inbound = intf[0]  # 0x2

        if self._dev.is_kernel_driver_active(self._interface):
            self._dev.detach_kernel_driver(self._interface)
        usb.util.claim_interface(self._dev, self._interface)


    def init(self):
        """0x7F Init DSO"""

        send = message.Message(mark=message.DEBUG_MESSAGE_MARKER, command=0x7F)
        self._write(send)
        msg = self._read()
        if self._verbose:
            print("Init {}".format(msg))


    def read_file(self, filepath: str) -> bytes:
        """Read content from file"""

        send = message.Message(command=0x10)
        send.data.frombytes(bytes(filepath, 'ascii'))
        self._write(send)

        msg = self._read()
        data = msg.data
        if len(data) == 1 and data[0] == 0x00:
            data.pop(0)

        while msg.subcommand != 0x02:
            msg = self._read()
            data.extend(msg.data)

        checksum = data.pop()
        if message.make_sum(data) != checksum:
            raise ValueError("File Checksum Error ({} / {})".format(
                checksum, len(data)))

        return data.tobytes()


    def sample(self, chan: int) -> None:
        """Request sample data"""

        send = message.Message(command=0x02,
            subcommand=0x01,
            data=array('B', [chan]))

        self._write(send)
        time.sleep(.04) # delay for acquisition (0.1 sec will get error)


    def get_sample(self) -> array:
        """Get sample data"""

        msg = self._read_expect(command=0x82)
        if self._verbose:
            print(_read_sample_data_length(msg))

        data = array('B')

        while msg and msg.subcommand not in [
                message.SAMPLE_SUM_SUBCMD, message.SAMPLE_STOP_SUBCMD]:
            msg = self._read()
            if msg and msg.data:
                data.extend(msg.data[1:])

        return data


    def is_available(self) -> bool:
        """Check device avalibility"""

        if not self._dev:
            return False

        return True


    def lock_panel(self, lock: bool) -> None:
        """0x12 Lock panel"""

        send = message.Message(command=0x12, subcommand=0x01)
        flag = 0x00
        if lock:
            flag = 0x01
        send.data = array('B', [flag])

        if self._verbose:
            print("locking {}".format(send))
        self._write(send)


    def read_settings(self) -> None:
        """0x01 Read DSO settings"""

        send = message.Message(command=0x01, data=array('B'))
        if self._verbose:
            print("settings {} {}".format(send, len(send.data)))
        self._write(send)


    def echo(self, text=None) -> None:
        """0x00 Echo
All data bytes in the request are simply returned unchanged."""

        send = message.Message(command=0x00)
        if text:
            data = array('B')
            for char in text:
                data.append(ord(char))
            send.data = data

        if self._verbose:
            print("echo {}".format(send))
        self._write(send)


    def buzzer(self, duration: int) -> None:
        """0x44 DSO Buzzer (debug)
Activates the DSO's buzzer for a period of time corresponding to the value specified * 100ms."""

        if duration > 255:
            duration = 255
        elif duration < 1:
            duration = 1
        send = message.Message(
            mark=message.DEBUG_MESSAGE_MARKER,
            command=0x44,
            data=array('B', [duration]))
        if self._verbose:
            print("buzz {}".format(send))
        self._write(send)


    def set_system_time(self) -> None:
        """0x14 Set system time
To current time"""

        now = datetime.now()
        data = array('B',[
            now.year & 0xff,
            now.year >> 8,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second,
        ])
        send = message.Message(command=0x14, data=data)

        if self._verbose:
            print("set time {}".format(send))
        self._write(send)


    def get_settings(self) -> array:
        """Get settings data"""

        msg = self._read_expect(command=0x81)
        if not msg or msg.command != 0x81:
            warnings.warn('No settings response: {}'.format(msg))

        return msg.data


    def close(self) -> None:
        """Release USB device"""

        usb.util.release_interface(self._dev, self._interface)


    def _read_expect(self, command: int = None, data: array = None) -> message.Message:

        last_msg = None
        try_count = 5
        while try_count > 0:
            try_count -= 1

            msg = self._read()
            if not msg:
                self.echo()
                continue

            last_msg = msg

            if command and msg.command != command:
                if self._verbose:
                    print("ignored {}".format(msg))
                continue

            if data and msg.data != data:
                continue

            break

        if not msg and last_msg:
            return last_msg

        return msg


    def _read(self) -> message.Message:

        pkt = array('B', [0]) * 0x8000
        try_count = 2
        while try_count > 0:
            try:
                self._dev.read(self._outbound.bEndpointAddress, pkt)
                break
            except usb.core.USBTimeoutError:
                if self._verbose:
                    print("timeout")
                try_count -= 1
        if self._verbose:
            print("read {}".format(pkt[:pkt[1]+5]))

        return message.build(pkt)


    def _write(self, msg: message.Message) -> None:

        pkt = message.create_packet(msg)
        if self._verbose:
            print(" - writing {}".format(pkt))
        self._dev.write(self._inbound.bEndpointAddress, pkt.tolist())


def _read_sample_data_length(msg: message.Message) -> str:

    if not msg:
        return ""

    out = "[SAMPLE] "
    if msg.command != 0x82:
        out += "It's not 0x82 command {}".format(msg)
        return out

    chan, length = _sample_data_length(msg.data)
    out += "CH:{} LEN:{}".format(chan+1, length)

    return out


def _sample_data_length(data: array):
    length = 0
    for idx, dat in enumerate(data[1:4]):
        length += dat << (8 * idx)
    return data[0], length


if __name__ == '__main__':

    ARGS = PARSER.parse_args()
    DEV = Dso(ARGS.verbose)

    if DEV.is_available():

        if ARGS.init:
            DEV.init()

        if ARGS.buzzer:
            DEV.buzzer(ARGS.buzzer)

        if ARGS.echo:
            DEV.echo(ARGS.echo)

        if ARGS.lock:
            DEV.lock_panel(True)

        if ARGS.settings:
            DEV.read_settings()
            DATA = DEV.get_settings()
            if DATA:
                print('Settings {}: {}'.format(len(DATA), DATA))
                if len(DATA) == 213:
                    with open("settings.dat", "w", encoding="utf8") as OUT:
                        for DAT in DATA:
                            OUT.write("{}\n".format(DAT))

        if ARGS.sample:
            CHAN = ARGS.sample -1
            DEV.sample(CHAN)
            DEV.echo("{}".format(CHAN))
            print(DEV.get_sample().tolist())

        if ARGS.set_time:
            DEV.set_system_time()

        if ARGS.unlock:
            DEV.lock_panel(False)

        DEV.close()

    else:

        print("DSO is not available")
