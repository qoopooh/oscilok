#!/usr/bin/env python
"""Get USB device info"""
from pprint import pprint
import usb


VENDOR = 0x049f
PRODUCT = 0x505a
devs = usb.core.find(find_all=True, idVendor=VENDOR, idProduct=PRODUCT)

for dev in devs:
    pprint(dev)
    print("bLength {}".format(dev.bLength))
    print("bNumConfigurations {}".format(dev.bNumConfigurations))
    print("bDeviceClass {}".format(dev.bDeviceClass))
    for cfg in dev:
        print("\tbConfigurationValue {}".format(cfg.bConfigurationValue))
        for intf in cfg:
            print("\tbInterfaceNumber {}".format(intf.bInterfaceNumber))
            print("\tbAlternateSetting {}".format(intf.bAlternateSetting))
            for ep in intf:
                print("\t\tbEndpointAddress {}".format(ep.bEndpointAddress))
