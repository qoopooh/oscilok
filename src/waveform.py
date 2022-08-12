"""Analyze wave form"""
from array import array
from dataclasses import dataclass
from enum import Enum


PERCENT_TO_PEAK = 6

class WaveType(Enum):
    """Wave type"""

    UNKNOWN = 0
    SINE = 1
    SQUARE = 2


class Peak(Enum):
    """Peak state"""

    UNKNOWN = 0
    TP_ST = 1
    TP_END = 2
    BT_ST = 3
    BT_END = 4


@dataclass
class Wave:
    """Recording data"""

    data: list = None
    typ: WaveType = WaveType.UNKNOWN


@dataclass
class Dot:
    """Recording data"""

    time: int = None
    val: int = None
    peak: Peak = Peak.UNKNOWN


def is_top_sine_inside_top_square(sine: list, square: list):
    """Find the top sine inside top square"""

    if not sine or not square:
        return False

    top_start_sine_dot = None
    top_end_sine_dot = None
    for dot in sine[int(len(sine)/3):]:
        if dot.peak == Peak.TP_ST and not top_start_sine_dot:
            top_start_sine_dot = dot

        if dot.peak == Peak.TP_END and top_start_sine_dot:
            top_end_sine_dot = dot
            break

    for idx, dot in enumerate(square):

        if dot.peak == Peak.TP_END \
                 and dot.time > top_end_sine_dot.time \
                 and dot.time > top_start_sine_dot.time:

            top_start_dot = square[idx - 1]
            if top_start_dot.time < top_start_sine_dot.time:
                return True

            break

    return False


def has_signal(data: array) -> bool:
    """data is straight line"""

    if len(data) == 0:
        return False

    data = _average(data)
    top, bottom = _get_top_bottom(data)

    diff = top - bottom
    # print('has_signal {} ({} / {})'.format(diff, top, bottom))

    if diff < 20:
        return False

    return True


def get_wave_form(unsigned_data: array) -> Wave:
    """Get time and peak state"""

    data = _conv_sign(unsigned_data)
    #print('signed_data', len(data), data[:30])
    data = _average(data)
    #print('avg_data', len(data), data[:30])
    top, bottom = _get_top_bottom(data)
    margin = ((top - bottom) * PERCENT_TO_PEAK) / 100
    top_area = top - margin
    bottom_area = bottom + margin

    #print("get_wave_form {}/{} / {}/{}".format(top, top_area, bottom_area, bottom))

    first_dat = data[0]
    dot = Dot(0, first_dat)
    if first_dat > top_area:
        dot.peak = Peak.TP_ST
    elif first_dat < bottom_area:
        dot.peak = Peak.BT_ST

    out = [dot]
    for idx, val in enumerate(data):

        prev_dot = out[-1]

        if prev_dot.peak == Peak.TP_ST and val < top_area:
            dot = Dot(idx, val, Peak.TP_END)
            out.append(dot)
            continue

        if prev_dot.peak == Peak.TP_END and val < bottom_area:
            dot = Dot(idx, val, Peak.BT_ST)
            out.append(dot)
            continue

        if prev_dot.peak == Peak.BT_ST and val > bottom_area:
            dot = Dot(idx, val, Peak.BT_END)
            out.append(dot)
            continue

        if prev_dot.peak == Peak.BT_END and val > top_area:
            dot = Dot(idx, val, Peak.TP_ST)
            out.append(dot)
            continue

        if prev_dot.peak == Peak.UNKNOWN:
            if val > top_area:
                dot = Dot(idx, val, Peak.TP_ST)
                out.append(dot)
                continue

            if val < bottom_area:
                dot = Dot(idx, val, Peak.BT_ST)
                out.append(dot)
                continue

    return Wave(out, _get_wave_type(out))


def _get_wave_type(out: list) -> Wave:
    wave_type = WaveType.UNKNOWN

    # get sample full wave
    if len(out) > 8:
        full_wave = _get_last_wave(out)

        if _is_small_signal(full_wave):
            return wave_type

        if _is_sine_wave(full_wave):
            wave_type = WaveType.SINE

        elif _is_square_wave(full_wave):
            wave_type = WaveType.SQUARE

    return wave_type


def _is_small_signal(dots: list) -> bool:
        diff = abs(dots[0].val - dots[2].val)

        return diff < 50


def _is_sine_wave(dots: list) -> bool:
    """Check sine wave
    dots start with TP_ST and TP_END should be appeared within 30% of the half wave
    """

    half_wave_time = dots[2].time - dots[0].time
    top_end_time = int(half_wave_time * .35) + dots[0].time

    return dots[1].time < top_end_time


def _is_square_wave(dots: list) -> bool:
    """Check square wave
    dots start with TP_ST and TP_END should be appeared within 30% of the half wave
    """

    half_wave_time = dots[2].time - dots[0].time
    top_end_time = (half_wave_time * .8) + dots[0].time

    return top_end_time < dots[1].time


def _get_last_wave(data: list) -> list:
    """Get the last full wave that should not have the noise"""

    out = []
    for idx, dot in enumerate(reversed(data)):
        if dot.peak == Peak.BT_END:
            end_idx = len(data) - idx
            start_idx = end_idx - 4
            out = data[start_idx:end_idx]
            break

    return out


def _conv_sign(data: array) -> array:
    """Convert array('B') to array('b')"""

    out = array('b')
    for dat in data:
        out.append(_one_byte_sign(dat))

    return out


def _average(data: array, avg_len: int=16) -> array:
    """Make signal more smooth to avoid noise"""

    out = array(data.typecode)
    if len(data) <= avg_len:
        return out

    for idx in range(avg_len, len(data)):
        summary = 0
        for dat in data[idx-avg_len:idx]:
            summary += dat
        out.append(int(summary / avg_len))

    return out


def _one_byte_sign(num: int) -> int:
    """Convert unsigned byte to signed byte"""

    if num < 128:
        return num

    if num > 255:
        num &= 0xFF

    out = 128 - (num & 0x7F)

    return out * -1


def _get_top_bottom(data: array):

    top, bottom = data[0], data[0]

    for dat in data:
        if dat > top:
            top = dat
        if dat < bottom:
            bottom = dat

    return top, bottom
