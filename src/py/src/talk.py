import json
import os
import socket
import typing


class HyprTalk:
    def __init__(self, cmd: str):
        self._cmd = cmd

        self._socket = (
            f"{os.getenv('XDG_RUNTIME_DIR')}/"
            "hypr/"
            f"{os.getenv('HYPRLAND_INSTANCE_SIGNATURE')}/"
            ".socket.sock"
        )

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

    def _execute(self, cmd: str) -> str:
        cmd_b = cmd.encode()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(self._socket)
            sock.send(cmd_b)

            res_b = b""
            while r := sock.recv(8192):
                res_b += r

        res = res_b.decode()
        if res == b"unknown request":
            raise ValueError(f"talk> invalid command [{cmd}]")
        return res
