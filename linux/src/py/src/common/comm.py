import logging
import socket
import typing

logger = logging.getLogger(__name__)


class Comm:
    BUFFER_SIZE = 4096

    def __init__(self, soc: typing.Any):
        self._socket = soc

    def talk(self, msg: bytes) -> bytes:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(self._socket)
            sock.send(msg)

            res_b = b""
            while True:
                r = sock.recv(Comm.BUFFER_SIZE)
                res_b += r
                if len(r) < Comm.BUFFER_SIZE:
                    break

        return res_b
