import collections.abc as cabc
import logging
import pathlib
import sys
import typing

import abstraction
import fzf
import launch
import talk


class Holding:
    def __init__(self):
        self._name = "HOLD"
        self._name_workspace = abstraction.HyprWorkspace.name_from_special(self._name)

        self._fzf = fzf.Fzf(fzf_tiebreak="index")

    def workspace(self) -> abstraction.HyprWorkspace:
        return abstraction.HyprWorkspace.from_name(self._name_workspace)

    def push(self, window_curr: typing.Optional[abstraction.HyprWindow] = None) -> None:
        window_curr = window_curr or abstraction.HyprWindow.from_current()

        try:
            window_prev = self.window_previous_non_hold()
        except RuntimeError:
            window_prev = None

        if not self._is_on_hold(window_curr):
            window_curr.float_off()
            self.to_hold(window_curr)

        if window_prev:
            window_prev.focus()

    def to_hold(
        self, window: abstraction.HyprWindow, unfocus_apres: bool = True
    ) -> None:
        is_empty_hold = self._is_empty_hold()

        window.fullscreen_off()
        window.move_to_workspace(self._name_workspace)

        if is_empty_hold:
            window.group_on_toggle()
        else:
            window.group_on_move()

        if unfocus_apres:
            self.workspace_hold_toggle()

    def window_previous_non_hold(
        self,
        workspace: typing.Optional[abstraction.HyprWorkspace] = None,
    ) -> abstraction.HyprWindow:
        windows = abstraction.HyprWindow.windows(sort_by_focus=True)
        next(windows)  # pop the first (current) window

        for window in windows:
            if not self._is_on_hold(window):
                if not workspace:
                    return window
                if window.is_in_workspace(workspace):
                    return window

        raise RuntimeError("hold> no previous non-hold window")

    def windows_non_hold(self) -> cabc.Generator[abstraction.HyprWindow, None, None]:
        for window in abstraction.HyprWindow.windows():
            if not self._is_on_hold(window):
                yield window

    def focus_previous(self) -> abstraction.HyprWindow:
        try:
            window = self.window_previous_non_hold()
        except RuntimeError:
            return
        window.focus()

    def move_to_monitor_current(self) -> None:
        try:
            workspace = self.workspace()
        except ValueError:
            return

        if workspace.monitor != abstraction.HyprMonitor.from_current():
            self.workspace_hold_toggle()
            self.workspace_hold_toggle()

    def _is_empty_hold(self) -> bool:
        try:
            self.workspace()
        except ValueError:
            return True
        return False

    def _is_on_hold(self, window: abstraction.HyprWindow) -> bool:
        return window.is_in_workspace(self._name_workspace)

    def is_on_hold_now(self) -> bool:
        return self._is_on_hold(abstraction.HyprWindow.from_current())

    def workspace_hold_toggle(self) -> None:
        talk.HyprTalk(f"togglespecialworkspace {self._name}").execute_as_dispatch()

    def peak(self, use_adhoc_terminal: bool = True) -> None:
        windows = self._windows()
        if use_adhoc_terminal:
            next(windows)  # pop the terminal-window
        next(windows)  # pop the current window

        try:
            choice = self._fzf.choose_one([w.selection_prompt() for w in windows])
        except RuntimeError:
            return
        abstraction.HyprWindow.from_selection_prompt(choice).focus()

    def pull(self, use_adhoc_terminal: bool = True) -> None:
        while True:
            mode = input("hypr> mode? [a]ppend (default); [r]eplace ")
            if not mode or mode == "a":
                self.pull_append()
                break
            if mode == "r":
                self.pull_replace(use_adhoc_terminal=use_adhoc_terminal)
                break
            print(f"hypr> huh? what is [{mode}]?\n")

    def pull_append(self) -> None:
        workspace = abstraction.HyprWorkspace.from_current()

        for window in self.select_multi():
            window.group_off_move()
            window.move_to_workspace(workspace)

    def select_multi(self) -> cabc.Generator[abstraction.HyprWindow, None, None]:
        for choice in self._fzf.choose_multi(self._choices()):
            yield abstraction.HyprWindow.from_selection_prompt(choice)

    def pull_replace(self, use_adhoc_terminal: bool = True) -> None:
        workspace = (
            abstraction.HyprWorkspace.from_current()
        )  # must get current workspace a priori

        try:
            window_curr = (
                self.window_previous_non_hold(workspace=workspace)
                if use_adhoc_terminal
                else abstraction.HyprWindow.from_current(workspace=workspace)
            )
        except RuntimeError:  # no current window to replace, append instead
            self.pull_append()
            return

        window_terminal = (
            abstraction.HyprWindow.from_current() if use_adhoc_terminal else None
        )

        is_master = False
        if workspace.n_windows > 1:
            if window_curr.is_master(restore_focus=False):
                is_master = True
            if window_terminal:
                window_terminal.focus()

        window = self.select()
        if not window:
            # restore focus during possible is_master check(s)
            window_curr.focus()
            return

        self.to_hold(window_curr)
        window.group_off_move()
        window.move_to_workspace(workspace)
        if is_master:
            window.make_master()

    def select(self) -> abstraction.HyprWindow | None:
        try:
            choice = self._fzf.choose_one(self._choices())
        except RuntimeError:
            return None
        return abstraction.HyprWindow.from_selection_prompt(choice)

    def _choices(self) -> cabc.Sequence[str]:
        return [w.selection_prompt() for w in self._windows()]

    def _windows(self) -> cabc.Generator[abstraction.HyprWindow, None, None]:
        for j in abstraction.HyprWindow.windows_json(sort_by_focus=True):
            if j["workspace"]["name"] == self._name_workspace:
                yield abstraction.HyprWindow.from_json(j)

    def unhold(self) -> None:
        workspace = next(self.workspaces_non_hold())
        window = abstraction.HyprWindow.from_current()

        window.group_off_move()
        window.move_to_workspace(workspace)

    def workspaces_non_hold(
        self,
    ) -> cabc.Generator[abstraction.HyprWorkspace, None, None]:
        for workspace in abstraction.HyprWorkspace.workspaces():
            if workspace == self._name_workspace:
                continue
            yield workspace


if __name__ == "__main__":
    logging.basicConfig(
        format="%(module)s [%(levelname)s]> %(message)s", level=logging.INFO
    )

    if len(sys.argv) == 1:
        raise RuntimeError("hypr/hold> say what?")

    def main(mode: typing.Optional[str] = None) -> None:
        if mode == "push":
            Holding().push()
            return

        if mode == "peak-cmd":
            Holding().peak()
            return
        if mode == "peak":
            h = Holding()
            if not h.is_on_hold_now():
                h.workspace_hold_toggle()
                return
            cmd = f"python {pathlib.Path(__file__).resolve()} {mode}-cmd"
            launch.Launch.launch_foot(cmd)
            return

        if mode == "pull-append-cmd":
            Holding().pull_append()
            return
        if mode == "pull-append":
            h = Holding()
            if h.is_on_hold_now():
                h.unhold()
                return

            abstraction.HyprWindow.from_current().fullscreen_off()
            cmd = f"python {pathlib.Path(__file__).resolve()} {mode}-cmd"
            launch.Launch.launch_foot(cmd)
            return

        if mode == "pull-replace-cmd":
            Holding().pull_replace()
            return
        if mode == "pull-replace":
            abstraction.HyprWindow.from_current().fullscreen_off()
            cmd = f"python {pathlib.Path(__file__).resolve()} {mode}-cmd"
            launch.Launch.launch_foot(cmd)
            return

        if mode == "pull-cmd":
            Holding().pull()
            return
        if mode == "pull":
            cmd = f"python {pathlib.Path(__file__).resolve()} {mode}-cmd"
            launch.Launch.launch_foot(cmd)
            return

        if mode == "pull-inplace":
            Holding().pull(use_adhoc_terminal=True)
            return

        raise RuntimeError("what mode?")

    main(sys.argv[1])
