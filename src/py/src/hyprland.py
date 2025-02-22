import logging
import pathlib
import sys
import typing

import launch
import libhyprland as libhp
import libwm
from definition import DEFINITION

logger = logging.getLogger(__name__)


class Front:
    def __init__(self):
        self._management = libhp.ManagementHyprland()

    def workspace_switch(self, workspace: str) -> None:
        self._management.load()
        logger.info(f"hyprland> workspace [{workspace}]: switch")
        self._management.workspace_switch(workspace)

    def workspace_add_window_current(self, workspace: str) -> None:
        self._management.load()

        try:
            window = self._management.window_current()
        except libwm.WindowError:
            logger.warning("hyprland> no window to add to workspace, skipping...")
            return

        if self._management.workspace_of_window(window) == workspace:
            logger.warning(
                f"hyprland> [{window}] already on [{workspace}]; skipping..."
            )
            return

        logging.info(f"libhyprland> adding [{window}] to [{workspace}]")
        self._management.workspace_add_window(workspace, window)

    def hold_add_window_current(self) -> None:
        self._management.load()

        try:
            window = self._management.window_current()
        except libwm.WindowError:
            logger.warning("hyprland> no window to add to hold, skipping...")
            return

        try:
            window_prev = self._management.window_prev_nonhold()
        except libwm.WindowError:
            window_prev = None

        self._management.hold_add(window)
        libhp.HoldHyprland.toggle()
        if window_prev:
            logger.info(f"hyprland> window-prev [{window_prev}]: switch")
            window_prev.goto()

    def hold_split_cmd(self) -> None:
        self._management.load()
        workspace = self._management.workspace_current()
        for window in self._management.hold_choose_windows():
            workspace.add(self._management.hold_split(window))

    def hold_repeek_cmd(self) -> None:
        self._management.load()

        if self._management.hold.n_windows() <= 2:
            # first window := terminal-window for fzf
            # second window := current (most recent) window on hold
            logger.warning("hyprland/repeek> no window to repeek, skipping...")
            return

        try:
            window = self._management.choose_window(self._management.hold.windows()[2:])
        except libwm.WorkspaceError:
            logger.warning("hyprland/repeek> no window selected, skipping...")
            return

        logger.info(f"hyprland/repeek> [{window}]")
        window.goto()

    def window_prev_switch(self) -> None:
        self._management.load()

        try:
            window = self._management.window_prev_nonhold()
        except libwm.WindowError:
            logger.warning("hyprland> no previous window to switch to, skipping...")
            return

        logger.info(f"hyprland> window-prev [{window}]: switch")
        window.goto()

    def window_current_close(self) -> None:
        self._management.load()

        try:
            window_current = self._management.window_current()
        except libwm.WindowError:
            logger.warning("hyprland/close> nothing to close, skipping...")
            return

        try:
            window_prev = self._management.window_prev_nonhold()
        except libwm.WindowError:
            logger.info(f"hyprland/close> [{window_current}] (last non-hold window)")
            window_current.close()
            return

        logger.info(
            f"hyprland/close> [{window_current}], switching to [{window_prev}] afterwards"
        )
        window_current.close()
        window_prev.goto()

    def window_make_unique(self) -> None:
        self._management.load()

        workspace = self._management.workspace_current()

        if workspace.is_empty():
            logger.warning(
                f"hyprland/make-unique> [{workspace}] already empty, skipping..."
            )
            return

        if workspace.n_windows() == 1:
            logger.warning(
                f"hyprland/make-unique> [{workspace}] has 1 window only, skipping..."
            )
            return

        window = self._management.window_current()
        logger.info(f"hyprland/make-unique> keeping [{window}]")
        for w in workspace.windows():
            if w != window:
                self._management.hold_add(w)
        libhp.HoldHyprland.toggle()

    def window_replace_cmd(self) -> None:
        self._management.load()
        workspace = self._management.workspace_current()

        try:
            window = self._management.window_prev()  # first window is terminal
        except libwm.WindowError:
            logger.warning(
                "hyprland/replace> no window to replace, splitting from hold directly..."
            )
            for window in self._management.hold_choose_windows():
                workspace.add(self._management.hold_split(window))
            return

        try:
            window_new = self._management.hold_choose_window()
        except libwm.WorkspaceError:
            logger.warning(
                f"hyprland/replace> no window selected to replace [{window}], skipping..."
            )
            return

        logger.info(f"hyprland/replace>  [{window}] -> [{window_new}]")
        workspace.add(self._management.hold_split(window_new))
        self._management.hold_add(window)
        libhp.HoldHyprland.toggle()


if __name__ == "__main__":
    logging.basicConfig(**DEFINITION.LOG_CONFIG, level=logging.INFO)

    # pylint: disable=too-many-return-statements,too-many-branches
    def main(mode: typing.Optional[str], *args: str) -> None:
        if mode == "workspace-switch":
            Front().workspace_switch(*args)
            return
        if mode == "workspace-add-window-current":
            Front().workspace_add_window_current(*args)
            return

        if mode == "hold-repeek-cmd":
            Front().hold_repeek_cmd(*args)
            return
        if mode == "hold-peek":
            m = libhp.ManagementHyprland()
            m.load()
            if not m.hold_is_active():
                logger.info("hyprland> hold-peek")
                m.hold_peek()
                return
            cmd = f"python {pathlib.Path(__file__).resolve()} hold-repeek-cmd"
            launch.Launch.launch_foot(cmd)
            return

        if mode == "hold-add-window-current":
            Front().hold_add_window_current(*args)
            return

        if mode == "hold-split-cmd":
            Front().hold_split_cmd()
            return
        if mode == "hold-split":
            m = libhp.ManagementHyprland()
            m.load()
            if m.hold_is_active():
                m.workspace_current().add(m.hold_split(m.window_current()))
                return
            cmd = f"python {pathlib.Path(__file__).resolve()} {mode}-cmd"
            launch.Launch.launch_foot(cmd)
            return

        if mode == "window-previous-switch":
            Front().window_prev_switch(*args)
            return
        if mode == "window-current-close":
            Front().window_current_close(*args)
            return
        if mode == "window-make-unique":
            Front().window_make_unique()
            return

        if mode == "window-replace-cmd":
            Front().window_replace_cmd(*args)
            return
        if mode == "window-replace":
            cmd = f"python {pathlib.Path(__file__).resolve()} {mode}-cmd"
            launch.Launch.launch_foot(cmd)
            return

        logger.error(f"hyprland> unrecognized mode [{mode}], exiting...")
        raise RuntimeError("what mode?")

    main(*sys.argv[1:])
