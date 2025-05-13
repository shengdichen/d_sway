import json
import logging
import os
import typing

from common import comm

logger = logging.getLogger(__name__)


class HyprTalk:
    def __init__(self, cmd: str):
        self._cmd = cmd

        soc = (
            f"{os.getenv('XDG_RUNTIME_DIR')}/"
            "hypr/"
            f"{os.getenv('HYPRLAND_INSTANCE_SIGNATURE')}/"
            ".socket.sock"
        )
        logger.debug(f"talk/hyprland> socket [{soc}]")
        self._comm = comm.Comm(soc)

    def execute_to_str(self) -> str:
        return self._execute(self._cmd)

    def execute_to_json(self) -> typing.Any:
        cmd = self.cmd_as_json(self._cmd)
        return json.loads(self._execute(cmd))

    @staticmethod
    def cmd_as_json(cmd: str) -> str:
        return f"[j]/{cmd}"

    def execute_as_dispatch(self) -> str:
        res = self._execute(f"dispatch {self._cmd}")
        if res == "Invalid dispatcher":
            raise ValueError(f"talk> invalid dispatch-command [{self._cmd}]")
        return res

    def execute_as_layoutmsg(self) -> None:
        # NOTE:
        #   there is NO way to check execution success

        self._execute(f"dispatch layoutmsg {self._cmd}")

    def execute_as_setprop(self) -> None:
        # NOTE:
        #   there is NO way to check execution success

        self._execute(f"setprop {self._cmd}")

    def _execute(self, cmd: str) -> str:
        res = self._comm.talk(cmd.encode()).decode()
        if res == "unknown request":
            raise ValueError(f"talk> invalid command [{cmd}]")
        return res
