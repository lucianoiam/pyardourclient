"""
  Copyright © 2020 Luciano Iam <lucianito@gmail.com>

  This library is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This library is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this library.  If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio

from .message import Node, Message, TypedValue, ValueList, AddressList
from .websocket import ArdourWebsocket


class ArdourClient(ArdourWebsocket):

    def __init__(self, host: str = '127.0.0.1', port: int = 3818) -> None:
        super().__init__(host, port)
        self._req_msg_hash = None
        self._resp_queue = asyncio.Queue(maxsize=1)

    async def get_strip_gain(self, strip_id: int) -> float:
        return await self._send_and_recv_single(Node.STRIP_GAIN, (strip_id,))

    async def get_strip_pan(self, strip_id: int) -> float:
        return await self._send_and_recv_single(Node.STRIP_PAN, (strip_id,))

    async def get_strip_mute(self, strip_id: int) -> bool:
        return await self._send_and_recv_single(Node.STRIP_MUTE, (strip_id,))

    async def get_strip_plugin_enable(self, strip_id: int, plugin_id: int) -> bool:
        return await self._send_and_recv_single(Node.STRIP_PLUGIN_ENABLE, (strip_id, plugin_id,))

    async def get_strip_plugin_param_value(self, strip_id: int, plugin_id: int, param_id: int) -> TypedValue:
        return await self._send_and_recv_single(Node.STRIP_PLUGIN_PARAM_VALUE, (strip_id, plugin_id, param_id,))

    async def get_tempo(self) -> float:
        return await self._send_and_recv_single(Node.TRANSPORT_TEMPO)

    async def get_transport_roll(self) -> bool:
        return await self._send_and_recv_single(Node.TRANSPORT_ROLL)

    async def get_record_state(self) -> bool:
        return await self._send_and_recv_single(Node.TRANSPORT_RECORD)

    async def set_strip_gain(self, strip_id: int, db: float) -> None:
        await self._send(Node.STRIP_GAIN, (strip_id,), (db,))

    async def set_strip_pan(self, strip_id: int, value: float) -> None:
        await self._send(Node.STRIP_PAN, (strip_id,), (value,))

    async def set_strip_mute(self, strip_id: int, value: bool) -> None:
        await self._send(Node.STRIP_MUTE, (strip_id,), (value,))

    async def set_strip_plugin_enable(self, strip_id: int, plugin_id: int, value: bool) -> None:
        await self._send(Node.STRIP_PLUGIN_ENABLE, (strip_id, plugin_id,), (value,))

    async def set_strip_plugin_param_value(self, strip_id: int, plugin_id: int, param_id: int, value: TypedValue) -> None:
        await self._send(Node.STRIP_PLUGIN_PARAM_VALUE, (strip_id, plugin_id, param_id,), (value,))
    
    async def set_tempo(self, bpm: float) -> None:
        await self._send(Node.TRANSPORT_TEMPO, (), (bpm,))

    async def set_transport_roll(self, value: bool) -> None:
        await self._send(Node.TRANSPORT_ROLL, (), (value,))

    async def set_record_state(self, value: bool) -> None:
        await self._send(Node.TRANSPORT_RECORD, (), (value,))

    async def receive(self):
        msg = await super().receive()
        # demux awaited request replies
        if self._req_msg_hash == msg.node_addr_hash():
            self._req_msg_hash = None
            await self._resp_queue.put(msg)
        return msg

    async def _send(self, node: Node, addr: AddressList = [], val: ValueList = []) -> Message:
        msg = Message(node, addr, val)
        await self.send(msg)
        return msg

    async def _send_and_recv(self, node: Node, addr: AddressList = [], val: ValueList = []) -> ValueList:
        req_msg = await self._send(node, addr, val)
        self._req_msg_hash = req_msg.node_addr_hash()
        resp_msg = await self._resp_queue.get()
        return resp_msg.val

    async def _send_and_recv_single(self, node: Node, addr: AddressList = [], val: ValueList = []) -> TypedValue:
        return (await self._send_and_recv(node, addr, val))[0]
