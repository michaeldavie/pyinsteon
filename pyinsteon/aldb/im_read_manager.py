"""Insteon Modem ALDB Read Manager."""
import asyncio
from ..handlers.get_first_all_link_record import GetFirstAllLinkRecordHandler
from ..handlers.get_next_all_link_record import GetNextAllLinkRecordHandler
from ..handlers.all_link_record_response import AllLinkRecordResponseHandler
from ..address import Address
from .aldb_record import ALDBRecord
from .control_flags import create_from_byte
from . import ModemALDB
from ..constants import ResponseStatus


class ImReadManager():
    """Insteon Modem ALDB Read Manager."""

    def __init__(self, aldb: ModemALDB):
        """Init the ImReadManager class."""
        self._aldb = aldb
        self._get_first_handler = GetFirstAllLinkRecordHandler()
        self._get_next_handler = GetNextAllLinkRecordHandler()
        self._receive_record_handler = AllLinkRecordResponseHandler()
        self._receive_record_handler.subscribe(self._receive_record)
        self._retries = 0
        self._load_lock = asyncio.Lock()

    def load(self):
        """Load the Insteon Modem ALDB."""
        asyncio.ensure_future(self.async_load())

    async def async_load(self):
        """Load the Insteon Modem ALDB."""
        response = False
        self._retries = 0
        await self._load_lock.acquire()
        while not response and not self._max_retries():
            response = await self._get_first_handler.async_send()
            self._retries += 1
        if response:
            await self._load_lock.acquire()
        if self._load_lock.locked():
            self._load_lock.release()
        return ResponseStatus.SUCCESS

    def _max_retries(self):
        """Test if max retries reached."""
        return self._retries >= 3

    def _receive_record(self, flags: bytes, group: int, address: Address,
                        data1: int, data2: int, data3: int):
        """Receive a record and load into the ALDB."""
        next_mem_addr = self._aldb.last_mem_addr - 8
        control_flags = create_from_byte(flags)
        record = ALDBRecord(next_mem_addr, control_flags, group, address,
                            data1, data2, data3)
        self._aldb[next_mem_addr] = record
        await self._get_next_record()

    async def _get_next_record(self):
        """Get the next ALDB record."""
        response = False
        self._retries = 0
        while not response and not self._max_retries():
            response = await self._get_next_handler.async_send()
            self._retries += 0
        if self._max_retries():
            self._load_lock.release()
