#!/usr/bin/env python
"""0x02 Read sample data
"""

import argparse
import sys
from array import array
import dso

CH1 = 0x01
CH2 = 0x02

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-c', '--channel', type=int,
    help='Reading channel (1 - CH1, 2 - CH2)',
    default=CH1,
    choices=[CH1, CH2])
PARSER.add_argument('-d', '--dual', help='Dual channels', action='store_true')
PARSER.add_argument('-v', '--verbose', help='verbose', action='store_true')


def read(channel: int, verbose=False) -> array:
    """Read sample data"""

    dev = dso.Dso(verbose)
    if not dev.is_available():
        print(dev.error)
        sys.exit()

    #0x02 Read sample data
    dev.sample(channel - 1)
    dev.echo()
    data = dev.get_sample()

    dev.close()

    return data


def _write_output(data: array, channel: int) -> None:

    print("data channel {} ({}): {}".format(channel, len(data), data.tolist()))

    with open("sample{}.dat".format(channel), "w", encoding="ascii") as outfile:
        for dat in data:
            outfile.write("{}\n".format(int(dat)))

    with open("sample_b{}.dat".format(channel), "wb") as outfile:
        outfile.write(data)


if __name__ == '__main__':

    ARGS = PARSER.parse_args()

    if ARGS.dual:

        DATA1 = read(ARGS.channel, ARGS.verbose)
        _write_output(DATA1, CH1)

        DATA2 = read(ARGS.channel, ARGS.verbose)
        _write_output(DATA2, CH2)

    else:

        DATA = read(ARGS.channel, ARGS.verbose)
        _write_output(DATA, ARGS.channel)
