import logging
import sys
import typing

import hold

logger = logging.getLogger(__name__)


def main(mode: typing.Optional[str] = None):
    if mode == "focus-previous":
        hold.Holding.focus_previous()
    else:
        raise RuntimeError("what mode?")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(module)s [%(levelname)s]> %(message)s", level=logging.INFO
    )

    if len(sys.argv) == 1:
        raise FloatingPointError("what mode? [push or pull?]")

    main(sys.argv[1])
