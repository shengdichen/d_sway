import collections.abc as cabc
import logging
import pathlib
import re
import sys
import typing

import abstraction
import fzf
import launch
import talk


class Holding:
    def __init__(self):
        self._pattern = re.compile(r"^.* \[ADDR: (.*)\].*$")
        self._fzf = fzf.Fzf(fzf_tiebreak="index")

        self._name_hold = abstraction.HyprWorkspace.name_from_special("HOLD")

    def push(self, window_curr: typing.Optional[abstraction.HyprWindow] = None) -> None:
        window_curr = window_curr or abstraction.HyprWindow.from_current()

        try:
            window_prev = Holding.window_previous_non_hold()
        except RuntimeError:
            window_prev = None

        window_curr.float_off()
        self._to_hold(window_curr)

        if window_prev:
            abstraction.HyprWindow.focus(window_prev)  # focus only if non-hold

    def _to_hold(
        self, window: abstraction.HyprWindow, unfocus_apres: bool = True
    ) -> None:
        is_empty_hold = self._is_empty_hold()

        window.fullscreen_off()
        window.move_window_to_workspace(self._name_hold)

        if is_empty_hold:
            window.group_on_toggle()
        else:
            window.group_on_move()

        if unfocus_apres:
            Holding.workspace_hold_toggle()

    @staticmethod
    def window_previous_non_hold(
        workspace: typing.Optional[abstraction.HyprWorkspace] = None,
    ) -> abstraction.HyprWindow:
        windows = abstraction.HyprWindow.windows(sort_by_focus=True)
        next(windows)  # pop the first (current) window

        for window in windows:
            if not window.workspace.is_workspace_hold():
                if not workspace:
                    return window
                if window.is_in_workspace(workspace):
                    return window

        raise RuntimeError("hold> no previous non-hold window")

    @staticmethod
    def focus_previous() -> abstraction.HyprWindow:
        try:
            window = Holding.window_previous_non_hold()
        except RuntimeError:
            return
        abstraction.HyprWindow.focus(window)

    def _is_empty_hold(self) -> bool:
        try:
            abstraction.HyprWorkspace.from_hold()
        except ValueError:
            return True
        return False

    @staticmethod
    def workspace_hold_toggle() -> None:
        talk.HyprTalk("togglespecialworkspace HOLD").execute_as_dispatch()

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
        for window in self.select_multi():
            window.group_off_move()
            window.move_to_current()

    def select_multi(self) -> cabc.Generator[abstraction.HyprWindow, None, None]:
        for choice in self._fzf.choose_multi(self._choices()):
            yield abstraction.HyprWindow.from_address(
                self._pattern.match(choice).group(1)
            )

    def pull_replace(self, use_adhoc_terminal: bool = True) -> None:
        workspace = (
            abstraction.HyprWorkspace.from_current()
        )  # must get current workspace a priori

        try:
            window_curr = (
                Holding.window_previous_non_hold(workspace=workspace)
                if use_adhoc_terminal
                else abstraction.HyprWindow.from_current_workspace(workspace)
            )
        except RuntimeError:
            self.pull_append()  # no current window to replace, append instead
            return

        window_terminal = (
            abstraction.HyprWindow.from_current() if use_adhoc_terminal else None
        )

        is_master = False
        if workspace.n_windows > 1:
            if window_curr.is_master(restore_focus=False):
                is_master = True
            if window_terminal:
                abstraction.HyprWindow.focus(window_terminal)

        window = self.select()
        if not window:
            # restore focus during possible is_master check(s)
            abstraction.HyprWindow.focus(window_curr)
            return

        self._to_hold(window_curr)
        window.group_off_move()
        window.move_window_to_workspace(workspace)
        if is_master:
            while not window.is_master():
                window.swap_within_workspace(positive_dir=False)

    def select(self) -> abstraction.HyprWindow | None:
        try:
            choice = self._fzf.choose_one(self._choices())
        except RuntimeError:
            return None
        return abstraction.HyprWindow.from_address(self._pattern.match(choice).group(1))

    def _choices(self) -> cabc.Sequence[str]:
        return [w.selection_prompt() for w in self._windows()]

    def _windows(self) -> cabc.Generator[abstraction.HyprWindow, None, None]:
        for j in abstraction.HyprWindow.windows_json(sort_by_focus=True):
            if j["workspace"]["name"] == self._name_hold:
                yield abstraction.HyprWindow.from_json(j)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(module)s [%(levelname)s]> %(message)s", level=logging.INFO
    )

    if len(sys.argv) == 1:
        raise RuntimeError("hypr/hold> say what?")

    def main(mode: typing.Optional[str] = None) -> None:
        if mode == "push":
            Holding().push()

        elif mode == "pull-append-cmd":
            Holding().pull_append()
        elif mode == "pull-append":
            cmd = f"python {pathlib.Path(__file__).resolve()} {mode}-cmd"
            launch.Launch.launch_foot(cmd)

        elif mode == "pull-replace-cmd":
            Holding().pull_replace()
        elif mode == "pull-replace":
            cmd = f"python {pathlib.Path(__file__).resolve()} {mode}-cmd"
            launch.Launch.launch_foot(cmd)

        elif mode == "pull-cmd":
            Holding().pull()
        elif mode == "pull":
            cmd = f"python {pathlib.Path(__file__).resolve()} {mode}-cmd"
            launch.Launch.launch_foot(cmd)

        elif mode == "pull-inplace":
            Holding().pull(use_adhoc_terminal=True)

        else:
            raise RuntimeError("what mode?")

    main(sys.argv[1])
