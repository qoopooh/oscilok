"""Test Message"""

import unittest
from array import array

import message


class TestStringMethods(unittest.TestCase):
    """Message tester"""

    def test_checksum(self):
        """Test checksum"""

        # 0x01 Read DSO settings
        pkt = array('B', [0x53, 0x02, 0x00, 0x01, 0x55])
        msg = message.build(pkt)
        self.assertFalse(msg.checksum)
        self.assertFalse(msg.response)

        pkt[-1] = 0x56
        msg = message.build(pkt)
        self.assertTrue(msg.checksum)


    def test_screenshot_cmd(self):
        """Test screenshot command"""

        pkt = array('B', [0x53, 0x02, 0x00, 0x20, 0x75])
        msg = message.build(pkt)

        self.assertEqual(msg.mark, message.NORMAL_MESSAGE_MARKER)
        self.assertEqual(msg.length, 2)
        self.assertEqual(msg.command, 0x20)
        self.assertEqual(msg.data, None)
        self.assertTrue(msg.checksum)


    def test_start_acquisition_cmd(self):
        """Start DSO acquisition command"""

        pkt = array('B', [0x53, 0x04, 0x00, 0x12, 0x00, 0x00, 0x69])
        msg = message.build(pkt)

        self.assertEqual(msg.mark, message.NORMAL_MESSAGE_MARKER)
        self.assertEqual(msg.length, 4)
        self.assertEqual(msg.command, 0x12)
        self.assertEqual(msg.subcommand, 0x00)
        self.assertEqual(msg.data, array('B', [0]))
        self.assertTrue(msg.checksum)
        self.assertFalse(msg.response)


    def test_stop_acquisition_cmd(self):
        """Stop DSO acquisition command"""

        pkt = array('B', [0x53, 0x04, 0x00, 0x12, 0x00, 0x01, 0x6a])
        msg = message.build(pkt)

        self.assertEqual(msg.data, array('B', [1]))
        self.assertTrue(msg.checksum)
        self.assertFalse(msg.response)


    def test_lock_control_panel_cmd(self):
        """Lock control panel command"""

        pkt = array('B', [0x53, 0x04, 0x00, 0x12, 0x01, 0x01, 0x6b])
        msg = message.build(pkt)

        self.assertEqual(msg.command, 0x12)
        self.assertEqual(msg.subcommand, 0x01)
        self.assertEqual(msg.data, array('B', [1]))
        self.assertTrue(msg.checksum)


    def test_unlock_control_panel_cmd(self):
        """Unlock control panel command"""

        pkt = array('B', [0x53, 0x04, 0x00, 0x12, 0x01, 0x00, 0x6a])
        msg = message.build(pkt)

        self.assertEqual(msg.data, array('B', [0]))
        self.assertTrue(msg.checksum)


    def test_keypress_autoset_cmd(self):
        """0x13 Keypress trigger: autoset"""

        pkt = array('B', [0x53, 0x04, 0x00, 0x13, 0x11, 0x01, 0x7c])
        msg = message.build(pkt)

        self.assertEqual(msg.command, 0x013)
        self.assertEqual(msg.length, 4)
        self.assertTrue(msg.checksum)
        self.assertFalse(msg.response)
        self.assertEqual(msg.data, array('B', [0x11, 0x01]))


    def test_create_screenshot_pkt(self):
        """Screenshot packet"""

        msg = message.Message(
            message.NORMAL_MESSAGE_MARKER,
            2,
            0x20
        )
        self.assertEqual(message.create_packet(msg),
            array('B', [0x53, 0x02, 0x00, 0x20, 0x75]))


if __name__ == '__main__':

    unittest.main()
