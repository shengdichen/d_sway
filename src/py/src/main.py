import logging
import sys
import typing

import abstraction
import hold

logger = logging.getLogger(__name__)


class Management:
    def __init__(self):
        pass

    def fullscreen(self) -> None:
        n_windows = abstraction.HyprWorkspace.from_current().n_windows
        if n_windows == 0:
            return
        if n_windows == 1:
            abstraction.HyprWindow.fullscreen_toggle(keep_decoration=False)
            return
        abstraction.HyprWindow.fullscreen_toggle()


def main(mode: typing.Optional[str] = None):
    if mode == "focus-previous":
        hold.Holding().focus_previous()
    elif mode == "fullscreen":
        Management().fullscreen()
    else:
        raise RuntimeError("what mode?")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(module)s [%(levelname)s]> %(message)s", level=logging.INFO
    )

    if len(sys.argv) == 1:
        raise RuntimeError("hypr/main> say what?")

    main(sys.argv[1])
