import logging
import pathlib
import sys
import typing

import hold
from abstraction import Launch

logger = logging.getLogger(__name__)


def main(mode: typing.Optional[str] = None):
    if mode == "push":
        hold.Holding().push()
    elif mode == "pull-terminal-curr":
        hold.Holding().pull(terminal_current=True)
    elif mode == "pull-terminal-new":
        hold.Holding().pull(terminal_current=False)
    elif mode == "pull":
        cmd = f"python {pathlib.Path(__file__).resolve()} pull-terminal-new"
        Launch.launch_foot(cmd)
    else:
        raise RuntimeError("what mode?")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(module)s [%(levelname)s]> %(message)s", level=logging.INFO
    )

    if len(sys.argv) == 1:
        raise FloatingPointError("what mode? [push or pull?]")

    main(sys.argv[1])
