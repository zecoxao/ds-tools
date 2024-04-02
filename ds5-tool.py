#!/usr/bin/env python3

import usb.core
import usb.util

import array
import struct
import sys
import binascii
import time
import hexdump
import argparse
from construct import *

class HID_REQ:
    DEV_TO_HOST = usb.util.build_request_type(
        usb.util.CTRL_IN, usb.util.CTRL_TYPE_CLASS, usb.util.CTRL_RECIPIENT_INTERFACE)
    HOST_TO_DEV = usb.util.build_request_type(
        usb.util.CTRL_OUT, usb.util.CTRL_TYPE_CLASS, usb.util.CTRL_RECIPIENT_INTERFACE)
    GET_REPORT = 0x01
    SET_REPORT = 0x09

VALID_DEVICE_IDS = [
    (0x054c, 0x0ce6),
]

class DS:

    def __init__(self):
        self.wait_for_device()

        if sys.platform != 'win32' and self.__dev.is_kernel_driver_active(0):
            try:
                self.__dev.detach_kernel_driver(0)
            except usb.core.USBError as e:
                sys.exit('Could not detatch kernel driver: %s' % str(e))

    def wait_for_device(self):
        print("Waiting for a DualSense...")
        while True:
            for i in VALID_DEVICE_IDS:
                self.__dev = usb.core.find(idVendor=i[0], idProduct=i[1])
                if self.__dev is not None:
                    print("Found a DualSense: vendorId=%04x productId=%04x" % (i[0], i[1]))
                    return
            time.sleep(1)
    
    def hid_get_report(self, report_id, size):
        dev = self.__dev
        #ctrl_transfer(bmRequestType, bRequest, wValue=0, wIndex=0, data_or_wLength=None, timeout=None)
        assert isinstance(size, int), 'get_report size must be integer'
        assert report_id <= 0xff, 'only support report_type == 0'
        return dev.ctrl_transfer(HID_REQ.DEV_TO_HOST, HID_REQ.GET_REPORT, report_id, 0, size + 1)[1:].tobytes()
    
    
    def hid_set_report(self, report_id, buf):
        dev = self.__dev
        assert isinstance(buf, (bytes, array.array)), 'set_report buf must be buffer'
        assert report_id <= 0xff, 'only support report_type == 0'
        buf = struct.pack('B', report_id) + buf
        return dev.ctrl_transfer(HID_REQ.HOST_TO_DEV, HID_REQ.SET_REPORT, (3 << 8) | report_id, 0, buf)
    
class Handlers:
    def __init__(self, dev):
        self.__dev = dev

    def info(self, args):
        info = self.__dev.hid_get_report(0x20, 0x10)
        print(info)

ds = DS()
handlers = Handlers(ds)

parser = argparse.ArgumentParser(description="Play with the DS controller",
                                 epilog="By the_al, modified by zeco, help for test by morteza")

subparsers = parser.add_subparsers(dest="action")

# Info
p = subparsers.add_parser('info', help="Print info about the DS")
p.set_defaults(func=handlers.info)

args = parser.parse_args()
if not hasattr(args, "func"):
    parser.print_help()
    exit(1)
args.func(args)
