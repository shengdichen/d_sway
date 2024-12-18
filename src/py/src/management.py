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
        self._monitor = abstraction.HyprMonitor.from_current()
        self._workspace = abstraction.HyprWorkspace.from_current()
        self._holding = hold.Holding()

    def focus_previous(self) -> None:
        self._holding.focus_previous()

    def fullscreen(self) -> None:
        n_windows = self._workspace.n_windows
        if n_windows <= 1:
            return
        abstraction.HyprWindow.from_current().fullscreen()

    def fullscreen_mode(self) -> None:
        n_windows = self._workspace.n_windows
        if n_windows == 0:
            return
        abstraction.HyprWindow.from_current().fullscreen_mode_switch()

    def make_only(self) -> None:
        n_windows = self._workspace.n_windows
        if n_windows in (0, 1):
            return

        window = abstraction.HyprWindow.from_current()
        for w in self._holding.windows_non_hold():
            if w != window and w.is_in_workspace(self._workspace):
                self._holding.to_hold(w)
        window.focus()

    def quit(self, stay_in_workspace: bool = False) -> None:
        try:
            if stay_in_workspace:
                window_prev = self._holding.window_previous_non_hold(
                    workspace=self._workspace
                )
            else:
                window_prev = self._holding.window_previous_non_hold()
        except RuntimeError:
            window_prev = None

        talk.HyprTalk("killactive").execute_as_dispatch()

        if window_prev:
            window_prev.focus()  # focus only if non-hold

    def window_to_workspace(self, workspace: str) -> None:
        if self._workspace.is_empty():
            return

        need_refocus = False
        if self._workspace.n_windows == 1:
            need_refocus = True

        window = abstraction.HyprWindow.from_current()
        if window.is_in_workspace(workspace):
            return
        window.move_to_workspace(workspace)

        if not need_refocus:
            return
        self._monitor_focus_workspace_previous()
        abstraction.HyprWorkspace.focus(workspace)

    def focus_to_workspace(self, workspace: str) -> None:
        if self._workspace == workspace:
            return

        try:
            ws = abstraction.HyprWorkspace.from_name(workspace)
        except ValueError:  # workspace does not exist
            abstraction.HyprWorkspace.focus(workspace)
            launch.Launch.launch_foot(use_footclient=True, as_float=False)
            return

        if ws.is_empty():  # workspace exists, but has no windows
            abstraction.HyprWorkspace.focus(ws)
            # force the focus-border to new workspace
            # (will otherwise remain in previous workspace, causing visual confusion)
            launch.Launch.launch_foot(use_footclient=True, as_float=False)
            return

        # sometimes hyprland's workspace-focus call (mysteriously) does not move
        # the focus-border to the new workspace; use the window-focus call instead
        abstraction.HyprWindow.from_previous_in_workspace(ws).focus()

    def workspace_to_monitor(self, monitor: str) -> None:
        self._monitor_focus_workspace_previous()

        self._move_workspace_to_monitor(monitor, self._workspace)
        abstraction.HyprWorkspace.focus(self._workspace)

    def _move_workspace_to_monitor(
        self,
        monitor: str,
        workspace: typing.Optional[abstraction.HyprWorkspace] = None,
    ) -> None:
        if workspace:
            cmd = f"moveworkspacetomonitor {workspace.name} {monitor}"
        else:
            cmd = f"movecurrentworkspacetomonitor {monitor}"
        talk.HyprTalk(cmd).execute_as_dispatch()

    def _monitor_focus_workspace_previous(self) -> None:
        for window in abstraction.HyprWindow.windows():
            if (
                window.is_on_monitor(self._monitor)
                and not window.is_in_workspace_special()
                and not window.is_in_workspace(self._workspace)
            ):
                abstraction.HyprWorkspace.focus(window.workspace)
                break

    def opacity(self) -> None:
        abstraction.HyprWindow.from_current().opacity_toggle()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(module)s [%(levelname)s]> %(message)s", level=logging.INFO
    )

    if len(sys.argv) == 1:
        raise RuntimeError("hypr/main> say what?")

    def main(mode: typing.Optional[str], *args: str) -> None:
        if mode == "focus-previous":
            Management().focus_previous()
        elif mode == "fullscreen":
            Management().fullscreen()
        elif mode == "fullscreen-mode":
            Management().fullscreen_mode()
        elif mode == "only":
            Management().make_only()
        elif mode == "quit":
            Management().quit()
        elif mode == "focus-to-workspace":
            Management().focus_to_workspace(*args)
        elif mode == "window-to-workspace":
            Management().window_to_workspace(*args)
        elif mode == "workspace-to-monitor":
            Management().workspace_to_monitor(*args)
        elif mode == "opacity":
            Management().opacity()
        else:
            raise RuntimeError("what mode?")

    main(*sys.argv[1:])
