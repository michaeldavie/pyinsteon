"""Handle an outbound direct message to a device."""

from abc import ABCMeta
import asyncio
from .outbound_base import OutboundHandlerBase
from ..address import Address
from . import ack_handler, direct_nak_handler, direct_ack_handler

TIMEOUT = 3  # Wait time for device response

class DirectCommandHandlerBase(OutboundHandlerBase):
    """Abstract base class for outbound direct message handling."""

    __meta__ = ABCMeta

    def __init__(self, address, command):
        """Init the DirectCommandHandlerBase class."""
        self._address = Address(address)
        self._response_lock = asyncio.Lock()
        super().__init__('{}.{}'.format(self._address.id, command))

    @property
    def response_lock(self) -> asyncio.Lock:
        """Lock to manage the response between ACK and Direct ACK."""
        return self._response_lock

    async def async_send(self, **kwargs):
        """Send the command and wait for a direct_nak."""
        if self.response_lock.locked():
            self.response_lock.release()
        await self.response_lock.acquire()
        response = await super().async_send(**kwargs)
        self.response_lock.release()
        return response

    @ack_handler(wait_direct_ack=True)
    def handle_ack(self, cmd2, target, user_data):
        """Handle the message ACK."""

    @direct_nak_handler
    def handle_direct_nak(self, cmd2, target, user_data):
        """Handle the message ACK."""

    @direct_ack_handler
    def handle_direct_ack(self, cmd2, target, user_data):
        """Handle the direct ACK."""
