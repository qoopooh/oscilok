"""Test Wave Form"""

import unittest

import waveform


class TestWaveFormMethods(unittest.TestCase):
    """WaveForm tester"""

    def test_last_wave(self):
        """Get the last full wave"""

        inp = [
            waveform.Dot(0, 20),
            waveform.Dot(10, 90, waveform.Peak.TP_ST),
            waveform.Dot(20, 88, waveform.Peak.TP_END),
            waveform.Dot(30, -91, waveform.Peak.BT_ST),
            waveform.Dot(40, -89, waveform.Peak.BT_END),
            waveform.Dot(110, 90, waveform.Peak.TP_ST),
            waveform.Dot(120, 88, waveform.Peak.TP_END),
            waveform.Dot(130, -91, waveform.Peak.BT_ST),
            waveform.Dot(140, -89, waveform.Peak.BT_END),
            waveform.Dot(210, 90, waveform.Peak.TP_ST),
            waveform.Dot(220, 88, waveform.Peak.TP_END),
            waveform.Dot(230, -91, waveform.Peak.BT_ST),
            waveform.Dot(240, -89, waveform.Peak.BT_END),
            waveform.Dot(260, 90, waveform.Peak.TP_ST),
            waveform.Dot(280, 88, waveform.Peak.TP_END),
            waveform.Dot(300, -91, waveform.Peak.BT_ST),
        ]
        out = [
            waveform.Dot(210, 90, waveform.Peak.TP_ST),
            waveform.Dot(220, 88, waveform.Peak.TP_END),
            waveform.Dot(230, -91, waveform.Peak.BT_ST),
            waveform.Dot(240, -89, waveform.Peak.BT_END),
        ]
        self.assertEqual(waveform._get_last_wave(inp), out)

    def test_sine_wave(self):
        """sine wave"""

        inp = [
            waveform.Dot(210, 90, waveform.Peak.TP_ST),
            waveform.Dot(215, 88, waveform.Peak.TP_END),
            waveform.Dot(230, -91, waveform.Peak.BT_ST),
            waveform.Dot(235, -89, waveform.Peak.BT_END),
        ]

        self.assertTrue(waveform._is_sine_wave(inp))
        self.assertFalse(waveform._is_square_wave(inp))

    def test_square_wave(self):
        """square wave"""

        inp = [
            waveform.Dot(210, 90, waveform.Peak.TP_ST),
            waveform.Dot(227, 88, waveform.Peak.TP_END),
            waveform.Dot(230, -91, waveform.Peak.BT_ST),
            waveform.Dot(247, -89, waveform.Peak.BT_END),
        ]

        self.assertTrue(waveform._is_square_wave(inp))
        self.assertFalse(waveform._is_sine_wave(inp))


if __name__ == '__main__':

    unittest.main()
