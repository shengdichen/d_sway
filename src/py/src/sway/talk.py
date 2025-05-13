import json
import logging
import os
import pathlib
import sys
import typing

from common import comm

logger = logging.getLogger(__name__)


class TalkErrorSway(RuntimeError):
    pass


class TalkSway:
    MAGIC = "i3-ipc"
    MAGIC_LENGTH = 6
    BUFFER_SIZE = 4096

    def __init__(self):
        soc = os.getenv("SWAYSOCK")
        if not pathlib.Path(soc).exists():
            raise TalkErrorSway
        logger.debug(f"talk/sway> socket [{soc}]")
        self._comm = comm.Comm(soc)

    def _execute(self, mode: int, arg: str = "") -> typing.Any:
        logger.debug(f"talk/sway> execute: mode [{mode}], arg ['{arg}']")
        res = TalkSway._disassemble(self._comm.talk(TalkSway._assemble(mode, arg)))
        logger.debug(f"talk/sway> result [{res}]")
        return res

    @staticmethod
    def _assemble(mode: int, arg: str) -> bytes:
        res = TalkSway.MAGIC.encode()

        res += len(arg).to_bytes(4, sys.byteorder)
        res += mode.to_bytes(4, sys.byteorder)
        res += arg.encode()

        return res

    @staticmethod
    def _disassemble(response: bytes) -> dict:
        response = response[TalkSway.MAGIC_LENGTH :]
        length = int.from_bytes(response[:4], byteorder=sys.byteorder)
        return json.loads(response[8 : 8 + length].decode("utf-8"))

    def execute(self, cmd: str) -> dict:
        return self._execute(0, cmd)

    def nodes(self) -> dict:
        return self._execute(4)

    def workspaces(self) -> dict:
        return self._execute(1)

    def monitors(self) -> dict:
        return self._execute(3)


talk = TalkSway()
