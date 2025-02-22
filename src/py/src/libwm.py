import collections.abc as cabc
import typing

import fzf


class Window:
    def __init__(
        self,
        identifier: typing.Any,
        #
        size_x: int,
        size_y: int,
        #
        class_initial: str,
        class_current: str,
        title_initial: str,
        title_current: str,
    ):  # pylint: disable=too-many-positional-arguments
        self._identifier = identifier
        self._size_x, self._size_y = size_x, size_y

        self._class_initial, self._class_current = class_initial, class_current
        self._title_initial, self._title_current = title_initial, title_current

    def __str__(self) -> str:
        return (
            f"window> {self._class_current}/{self._title_current} [{self._identifier}]"
        )

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, Window):
            return self._identifier == that._identifier
        return False

    def goto(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def opacity_toggle(self) -> None:
        pass

    def format_human(self) -> str:
        raise NotImplementedError

    @staticmethod
    def identifier_from_format_human(format_human: str) -> typing.Any:
        raise NotImplementedError


class WindowError(ValueError):
    pass


class Workspace:
    def __init__(self, identifier: typing.Any):
        self._identifier = identifier

        self._windows: list[Window] = []

    def __str__(self) -> str:
        return f"workspace> {self._identifier}, size {len(self._windows)}"

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, Workspace):
            return self._identifier == that._identifier
        return False

    def is_empty(self) -> bool:
        return not bool(self._windows)

    def n_windows(self) -> int:
        return len(self._windows)

    def has(self, window: Window) -> bool:
        return window in self._windows

    def add(self, window: Window) -> None:
        if not self.has(window):
            self._add(window)
            self._windows.append(window)

    def _add(self, window: Window) -> None:
        raise NotImplementedError

    @staticmethod
    def add_new(workspace: typing.Any, window: Window) -> None:
        """
        add window to new workspace
        """
        raise NotImplementedError

    def windows(self) -> list[Window]:
        return self._windows

    def window_current(self) -> Window:
        return self._windows[0]

    def goto(self) -> None:
        self.window_current().goto()

    @staticmethod
    def goto_new(workspace: typing.Any) -> None:
        """
        goto new workspace
        """
        raise NotImplementedError


class WorkspaceError(ValueError):
    pass


class Monitor:
    def __init__(
        self,
        identifier: typing.Any,
        #
        size_x: int,
        size_y: int,
    ):
        self._identifier = identifier
        self._size_x, self._size_y = size_x, size_y
        self._info = {
            "refresh_rate": 0,
            "is_vrr": False,
        }
        self._workspaces: list[Workspace] = []
        self._workspace_current: typing.Optional[Workspace] = None

    def __str__(self) -> str:
        return f"monitor> {self._identifier}: {self._size_x}x{self._size_y}"

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, Monitor):
            return self._identifier == that._identifier
        return False

    def add(self, workspace: Workspace) -> None:
        if not self.has(workspace):
            self._workspaces.append(workspace)

    def set_current(self, workspace: Workspace) -> None:
        self._workspace_current = workspace

    def get_current(self) -> typing.Optional[Workspace]:
        return self._workspace_current

    def has(self, workspace: Workspace) -> bool:
        return workspace in self._workspaces

    def workspaces(self) -> list[Workspace]:
        return self._workspaces


class MonitorError(ValueError):
    pass


class Management:
    def __init__(self):
        self._monitors: list[Monitor] = []  # type: ignore [annotation-unchecked]
        self._workspaces: list[Workspace] = []  # type: ignore [annotation-unchecked]

        # order: recently visited
        self._windows: list[Window] = []  # type: ignore [annotation-unchecked]

    def load_monitors(self) -> None:
        raise NotImplementedError

    def load_workspaces(self) -> None:
        raise NotImplementedError

    def load_windows(self) -> None:
        raise NotImplementedError

    def load(self) -> None:
        self.load_monitors()
        self.load_workspaces()
        self.load_windows()

    def status(self) -> None:
        for monitor in self._monitors:
            print(monitor, monitor.get_current())
        for workspace in self._workspaces:
            print(workspace)
        for window in self._windows:
            print(window)

    def monitor_exists(self, query: typing.Any) -> bool:
        return query in self._monitors

    def monitor_find(self, query: typing.Any) -> Monitor:
        for monitor in self._monitors:
            if monitor == query:
                return monitor
        raise MonitorError

    def monitor_of_workspace(self, workspace: Workspace) -> Monitor:
        for monitor in self._monitors:
            if monitor.has(workspace):
                return monitor
        raise MonitorError

    def workspace_exists(self, query: typing.Any) -> bool:
        return query in self._workspaces

    def workspace_find(self, query: typing.Any) -> Workspace:
        for workspace in self._workspaces:
            if workspace == query:
                return workspace
        raise WorkspaceError

    def workspace_of_window(self, window: Window) -> Workspace:
        for workspace in self._workspaces:
            if workspace.has(window):
                return workspace
        raise WorkspaceError

    def workspace_switch(self, workspace: typing.Any) -> None:
        for ws in self._workspaces:
            if ws == workspace:
                ws.goto()
                return
        self._workspace_new(workspace)

    def _workspace_new(self, workspace: typing.Any) -> None:
        raise NotImplementedError

    def workspace_add_window(self, workspace: typing.Any, window: Window) -> None:
        for ws in self._workspaces:
            if ws == workspace:
                ws.add(window)
                return
        self._workspace_new_add_window(workspace, window)

    def _workspace_new_add_window(self, workspace: typing.Any, window: Window) -> None:
        raise NotImplementedError

    def workspace_current(self) -> Workspace:
        raise NotImplementedError

    def choose_windows(
        self, windows: cabc.Iterable[Window]
    ) -> cabc.Generator[Window, None, None]:
        f = fzf.Fzf(fzf_tiebreak="index")
        for format_human in f.choose_multi((w.format_human() for w in windows)):
            yield self._window_from_format_human(format_human)

    def choose_window(self, windows: cabc.Iterable[Window]) -> Window:
        f = fzf.Fzf(fzf_tiebreak="index")
        format_human = f.choose_one((w.format_human() for w in windows))
        return self._window_from_format_human(format_human)

    def _window_from_format_human(self, format_human: typing.Any) -> Window:
        raise NotImplementedError

    def window_current(self) -> Window:
        if not self._windows:
            raise WindowError("libwm> no current window")
        return self._windows[0]

    def window_prev(self) -> Window:
        try:
            window = self._windows[1]
        except IndexError as e:
            raise WindowError("libwm> no previous window") from e
        return window

    def window_prev_nonhold(self) -> Window:
        raise NotImplementedError

    def window_is_onhold(self, window: Window) -> bool:
        raise NotImplementedError

    def hold_is_active(self) -> bool:
        raise NotImplementedError

    def hold_peek(self) -> None:
        raise NotImplementedError

    def hold_add(self, window: Window) -> None:
        raise NotImplementedError

    def hold_split(self, window: Window) -> Window:
        raise NotImplementedError

    def hold_choose_windows(self) -> cabc.Iterable[Window]:
        raise NotImplementedError

    def hold_choose_window(self) -> Window:
        raise NotImplementedError
