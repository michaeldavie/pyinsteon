"""Manage getting an operating flag."""
import asyncio
from collections import namedtuple
import logging

from ..address import Address
from ..handlers.to_device.get_operating_flags import GetOperatingFlagsCommand
from ..handlers.to_device.set_operating_flags import SetOperatingFlagsCommand
from ..utils import multiple_status
from ..constants import ResponseStatus


OperatingFlagInfo = namedtuple("FlagInfo", "name group bit set_cmd unset_cmd")
_LOGGER = logging.getLogger(__name__)
MAX_RETRIES = 5


class GetSetOperatingFlagsManager:
    """Manager to get operating flags."""

    def __init__(self, address: Address, op_flags):
        """Init the GetOperatingFlagsManager class."""
        self._address = Address(address)
        self._op_flags = op_flags
        self._groups = {}
        self._flags = {}
        self._get_command = GetOperatingFlagsCommand(self._address)
        self._set_command = SetOperatingFlagsCommand(self._address)
        self._get_command.subscribe(self._update_flags)
        self._send_lock = asyncio.Lock()

    def subscribe(self, name, group, bit, set_cmd, unset_cmd):
        """Subscribe to updates."""
        flag_info = OperatingFlagInfo(name, group, bit, set_cmd, unset_cmd)
        if self._groups.get(group) is None:
            self._groups[group] = {}
        if bit is not None:
            self._groups[group][bit] = flag_info
        else:
            self._groups[group] = flag_info
        self._flags[name] = flag_info

    def unsubscribe(self, name):
        """Remove a flag from updates."""
        flag_info = self._flags.get(name)
        if flag_info:
            group = flag_info.group
            bit = flag_info.bit
            self._remove(name, group, bit)

    def _remove(self, name, group, bit=None):
        try:
            if bit is not None:
                self._groups[group].pop(bit)
            else:
                self._groups.pop(group)
        except KeyError:
            pass

        try:
            self._flags.pop(name)
        except KeyError:
            pass

    async def async_read(self, group=None):
        """Get the operating flags."""
        results = []
        if group is None:
            for curr_group in self._groups:
                result = await self._async_read(curr_group)
                results.append(result)
            return multiple_status(*results)
        return await self._async_read(group)

    async def _async_read(self, group):
        retries = 0
        result = ResponseStatus.UNSENT
        while retries < MAX_RETRIES and result != ResponseStatus.SUCCESS:
            result = await self._get_command.async_send(group)
            retries += 1
        return result

    async def async_write(self):
        """Set the operating flags."""
        results = []
        for name in self._op_flags:
            if self._op_flags[name].is_dirty:
                flat_info = self._flags[name]
                result = await self._async_write(flat_info)
                results.append(result)

    async def _async_write(self, flag_info):
        flag = self._op_flags[flag_info.name]
        cmd = flag_info.set_cmd if flag.new_value else flag_info.unset_cmd
        if cmd is not None:  # The operating flag is read only
            retries = 0
            result = ResponseStatus.UNSENT

            while retries < MAX_RETRIES and result != ResponseStatus.SUCCESS:
                result = await self._set_command.async_send(cmd=cmd)
                retries += 1

            if result == ResponseStatus.SUCCESS:
                flag.load(flag.new_value)
            return result

        # Reset the read only flag to original value
        flag.load(flag.value)
        return ResponseStatus.SUCCESS

    def _update_flags(self, group, flags):
        """Update each flag."""
        if not self._groups.get(group):
            return

        if isinstance(self._groups[group], OperatingFlagInfo):
            flag_info = self._groups[group]
            flag = self._op_flags[flag_info.name]
            flag.load(flags)

        for bit in self._groups[group]:
            flag_info = self._groups[group][bit]
            flag = self._op_flags[flag_info.name]
            value = bool(flags & 1 << flag_info.bit)
            flag.load(value)