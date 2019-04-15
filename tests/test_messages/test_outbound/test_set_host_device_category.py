from binascii import unhexlify
import logging
import unittest
import sys

from pyinsteon.constants import MessageId, DeviceCategory
from pyinsteon.protocol.messages.outbound import set_host_dev_cat
from tests.test_messages.test_outbound.outbound_base import TestOutboundBase


_LOGGER = logging.getLogger(__name__)
_INSTEON_LOGGER = logging.getLogger('pyinsteon')


class TestSetHostDeviceCategory(unittest.TestCase, TestOutboundBase):

    def setUp(self):
        self.hex = '0266030405'
        self.bytes_data = unhexlify(self.hex)
        self.message_id = MessageId.SET_HOST_DEV_CAT
        self.cat = DeviceCategory(0x03)
        self.subcat = int(0x04)
        self.firmware = int(0x05)

        kwargs = {'cat': self.cat,
                  'subcat': self.subcat,
                  'firmware': self.firmware}

        super(TestSetHostDeviceCategory, self).base_setup(self.message_id,
                                                          unhexlify(self.hex),
                                                          **kwargs)

        stream_handler = logging.StreamHandler(sys.stdout)
        _LOGGER.addHandler(stream_handler)

    def test_cat(self):
        assert self.msg.cat == self.cat

    def test_subcat(self):
        assert self.msg.subcat == self.subcat

    def test_firmware(self):
        assert self.msg.firmware == self.firmware


if __name__ == '__main__':
    unittest.main()