import logging
import sys
import typing

import abstraction
import hold
import launch
import talk

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

    def quit(self, stay_in_workspace: bool = False) -> None:
        try:
            if stay_in_workspace:
                window_prev = hold.Holding().window_previous_non_hold(
                    workspace=abstraction.HyprWorkspace.from_current()
                )
            else:
                window_prev = hold.Holding().window_previous_non_hold()
        except RuntimeError:
            window_prev = None

        talk.HyprTalk("killactive").execute_as_dispatch()

        if window_prev:
            window_prev.focus()  # focus only if non-hold

    def to_workspace(self, workspace: str) -> None:
        try:
            ws = abstraction.HyprWorkspace.from_name(workspace)
        except ValueError:
            talk.HyprTalk(f"workspace {workspace}").execute_as_dispatch()
            launch.Launch.launch_foot(use_footclient=True, as_float=False)
            return

        talk.HyprTalk(f"workspace {workspace}").execute_as_dispatch()
        if ws.n_windows == 0:
            launch.Launch.launch_foot(use_footclient=True, as_float=False)


def main(mode: typing.Optional[str], *args: str):
    if mode == "focus-previous":
        hold.Holding().focus_previous()
    elif mode == "fullscreen":
        Management().fullscreen()
    elif mode == "quit":
        Management().quit()
    elif mode == "workspace":
        Management().to_workspace(*args)
    else:
        raise RuntimeError("what mode?")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(module)s [%(levelname)s]> %(message)s", level=logging.INFO
    )

    if len(sys.argv) == 1:
        raise RuntimeError("hypr/main> say what?")

    main(*sys.argv[1:])
