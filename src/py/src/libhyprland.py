import collections.abc as cabc
import logging
import re
import time
import typing

import launch
import libwm
import prettyprint
import talk

logger = logging.getLogger(__name__)


class WindowHyprland(libwm.Window):
    PATTERN_SELECTION_PROMPT = re.compile(r"^.* (0x[0-9a-f]*)$")

    def __init__(
        self,
        identifier: str,  # str-repr of hex-int
        #
        size_x: int,
        size_y: int,
        #
        class_initial: str,
        class_current: str,
        title_initial: str,
        title_current: str,
    ):  # pylint: disable=too-many-positional-arguments
        super().__init__(
            identifier=identifier,
            size_x=size_x,
            size_y=size_y,
            #
            class_initial=class_initial,
            class_current=class_current,
            title_initial=title_initial,
            title_current=title_current,
        )

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, str):
            return self._identifier == that
        return super().__eq__(that)

    @classmethod
    def from_json(cls, j: dict) -> "WindowHyprland":
        size_x, size_y = j["size"]
        return cls(
            identifier=j["address"],
            #
            size_x=size_x,
            size_y=size_y,
            #
            class_initial=j["initialClass"],
            class_current=j["class"],
            title_initial=j["initialTitle"],
            title_current=j["title"],
        )

    @classmethod
    def from_json_current(cls) -> "WindowHyprland":
        return cls.from_json(WindowHyprland.json_current())

    @staticmethod
    def jsons() -> list[dict]:
        return talk.HyprTalk("clients").execute_to_json()

    @staticmethod
    def jsons_by_time() -> cabc.Generator[dict, None, None]:
        yield from sorted(WindowHyprland.jsons(), key=lambda _j: _j["focusHistoryID"])

    @staticmethod
    def json_current() -> dict:
        return talk.HyprTalk("activewindow").execute_to_json()

    @classmethod
    def from_footclient(cls) -> "WindowHyprland":
        launch.Launch.launch_foot(use_footclient=True, as_float=False)

        cadence = 0.1
        while True:
            if j := WindowHyprland.json_current():
                return cls.from_json(j)
            logger.info(f"window/hyprland> waiting {cadence} for hyprland to catchup")
            time.sleep(cadence)

    def as_addr(self) -> str:
        return f"address:{self._identifier}"

    def goto(self) -> None:
        logger.debug(f"window/hyprland> goto [{self}]")
        cmd = f"focuswindow {self.as_addr()}"
        talk.HyprTalk(cmd).execute_as_dispatch()

    def close(self) -> None:
        logger.debug(f"window/hyprland> close [{self}]")
        cmd = f"closewindow {self.as_addr()}"
        talk.HyprTalk(cmd).execute_as_dispatch()

    def format_human(self) -> str:
        greyer = prettyprint.Prettyprint().color_foreground("grey-bright")

        str_class = (
            f"{self._class_current.split('.')[-1] if self._class_current else 'class?'}"
        )
        if str_class == "firefox-developer-edition":
            str_class = "firefoxd"
        str_class = f"{prettyprint.Prettyprint().cyan(str_class)}{greyer.apply('>')}"

        str_title = self._title_current or "title?"

        str_addr = (
            f"{greyer.apply(f'// {self._identifier[:2]}')}"
            f"{greyer.decorate_underline().apply(self._identifier[2:])}"
        )

        return f"{str_class} {str_title}  {str_addr}"

    @staticmethod
    def identifier_from_format_human(format_human: str) -> str:
        m = WindowHyprland.PATTERN_SELECTION_PROMPT.match(format_human)
        if not m:
            raise RuntimeError(f"window> invalid choice {format_human}")
        return m.group(1)

    def is_grouped(self) -> bool:
        for j in WindowHyprland.jsons():
            if j["address"] == self:
                return bool(j["grouped"])
        raise libwm.WindowError

    def group_join(self) -> None:
        if self.is_grouped():
            logger.warning(f"window/hyprland> [{self}] is already grouped, skipping...")
            return

        for d in "lrud":
            talk.HyprTalk(f"moveintogroup {d}").execute_as_dispatch()
            if self.is_grouped():
                logger.info(
                    f"window/hyprland> [{self}] is grouped after moving in direction [{d}], done!"
                )
                break
            logger.debug(
                f"window/hyprland> [{self}] is not grouped after moving in direction "
                f"[{d}], continuing on..."
            )

    def group_leave(self) -> None:
        if not self.is_grouped():
            logger.warning(
                f"window/hyprland> [{self}] is not grouped already, skipping..."
            )
            return

        logger.info(f"window/hyprland> [{self}] ungrouping")
        talk.HyprTalk(
            f"moveoutofgroup address:{self._identifier}"
        ).execute_as_dispatch()

    def group_toggle(self) -> None:
        logger.debug(f"window/hyprland> toggle window-grouping [{self}]")
        talk.HyprTalk("togglegroup").execute_as_dispatch()

    def get_pos(self) -> tuple[int, int]:
        for j in WindowHyprland.jsons_by_time():
            if j["address"] == self:
                return j["at"]
        raise libwm.WindowError


class WorkspaceHyprland(libwm.Workspace):
    def __init__(self, identifier: int, name: str):
        super().__init__(identifier=identifier)
        self._name = name

    def __str__(self) -> str:
        return (
            f"workspace> {self._identifier}.'{self._name}', size {len(self._windows)}"
        )

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, int):
            return self._identifier == that
        if isinstance(that, str):
            return self._name == that
        return super().__eq__(that)

    @classmethod
    def from_json(cls, j: dict) -> "WorkspaceHyprland":
        return cls(identifier=j["id"], name=j["name"])

    @staticmethod
    def jsons() -> cabc.Sequence[dict]:
        return talk.HyprTalk("workspaces").execute_to_json()

    @staticmethod
    def json_current() -> dict:
        return talk.HyprTalk("activeworkspace").execute_to_json()

    def add(self, window: WindowHyprland) -> None:
        logger.info(f"workspace/hyprland> [{self}]: adding [{window}]")
        super().add(window)

    def _add(self, window: WindowHyprland) -> None:
        cmd = f"movetoworkspace {self._name},{window.as_addr()}"
        talk.HyprTalk(cmd).execute_as_dispatch()

    @staticmethod
    def add_new(workspace: typing.Any, window: WindowHyprland) -> None:
        logger.info(f"workspace/hyprland> new [{workspace}]: adding [{window}]")
        cmd = f"movetoworkspace {workspace},{window.as_addr()}"
        talk.HyprTalk(cmd).execute_as_dispatch()

    def goto(self) -> None:
        logger.debug(f"workspace/hyprland> goto [{self}]")
        cmd = f"workspace {self._identifier}"
        talk.HyprTalk(cmd).execute_as_dispatch()
        if self.is_empty():
            launch.Launch.launch_foot(use_footclient=True, as_float=False)

    @staticmethod
    def goto_new(workspace: typing.Any) -> None:
        logger.debug(f"workspace/hyprland> goto-new [{workspace}]")
        cmd = f"workspace {workspace}"
        talk.HyprTalk(cmd).execute_as_dispatch()
        WindowHyprland.from_footclient()


class HoldHyprland(libwm.Workspace):
    NAME = "HOLD"
    NAME_FULL = f"special:{NAME}"

    def __init__(self, identifier: int):
        super().__init__(identifier=identifier)

    def __str__(self) -> str:
        return f"hold/hyprland> size {len(self._windows)} [id: {self._identifier}]"

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, int):
            return self._identifier == that
        if isinstance(that, str):
            return HoldHyprland.NAME_FULL == that
        return super().__eq__(that)

    @staticmethod
    def is_hold(name: str) -> bool:
        return HoldHyprland.NAME_FULL == name

    @classmethod
    def from_json(cls, j: dict) -> "HoldHyprland":
        return cls(identifier=j["id"])

    def add(self, window: WindowHyprland) -> None:
        logger.info(f"hold/hyprland> adding [{window}]")
        super().add(window)

    def _add(self, window: WindowHyprland) -> None:
        cmd = f"movetoworkspace {HoldHyprland.NAME_FULL},{window.as_addr()}"
        talk.HyprTalk(cmd).execute_as_dispatch()
        window.group_join()

    @staticmethod
    def add_new(window: WindowHyprland) -> None:
        logger.info(f"hold/hyprland> currently empty, adding [{window}]")
        cmd = f"movetoworkspace {HoldHyprland.NAME_FULL},{window.as_addr()}"
        talk.HyprTalk(cmd).execute_as_dispatch()
        window.group_toggle()

    def split(self, window: WindowHyprland) -> WindowHyprland:
        logger.info(f"hold/hyprland> splitting [{window}]")
        window.group_leave()
        self._windows.remove(window)
        return window

    @staticmethod
    def show() -> None:
        monitor_id = WorkspaceHyprland.json_current()["monitorID"]

        for j in talk.HyprTalk("monitors").execute_to_json():
            if j["specialWorkspace"]["name"] != HoldHyprland.NAME_FULL:
                continue
            if j["id"] == monitor_id:
                logger.warning("hold/hyprland> showing already, skipping...")
                return
            logger.info(
                f"hold/hyprland> currently on monitor [{j['id']}]"
                f", now showing on monitor [{monitor_id}]"
            )
            HoldHyprland.toggle()
            return

        logger.info(f"hold/hyprland> showing for monitor [{monitor_id}]")
        HoldHyprland.toggle()

    @staticmethod
    def hide() -> None:
        monitor_id = WorkspaceHyprland.json_current()["monitorID"]

        for j in talk.HyprTalk("monitors").execute_to_json():
            if j["specialWorkspace"]["name"] != HoldHyprland.NAME_FULL:
                continue
            if j["id"] == monitor_id:
                logger.info(
                    f"hold/hyprland> on current monitor [{monitor_id}]"
                    ", toggling once to turn off"
                )
                HoldHyprland.toggle()
                return
            logger.info(
                f"hold/hyprland> currently on another monitor [{j['id']}]"
                ", toggling twice to turn off"
            )
            HoldHyprland.toggle()  # make visible on current monitor...
            HoldHyprland.toggle()  # ...then turn off
            return

        logger.warning("hold/hyprland> off already, skipping...")

    @staticmethod
    def toggle() -> None:
        logger.debug("hold/hyprland> toggling")
        talk.HyprTalk(
            f"togglespecialworkspace {HoldHyprland.NAME}"
        ).execute_as_dispatch()


class MonitorHyprland(libwm.Monitor):
    def __init__(
        self,
        identifier: int,
        name: str,
        #
        size_x: int,
        size_y: int,
    ):
        super().__init__(
            identifier=identifier,
            size_x=size_x,
            size_y=size_y,
        )
        self._name = name

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, int):
            return self._identifier == that
        return super().__eq__(that)

    @classmethod
    def from_json(cls, js: dict) -> "MonitorHyprland":
        return cls(
            identifier=js["id"],
            name=js["name"],
            #
            size_x=js["width"],
            size_y=js["height"],
        )


class Geometry:
    def window_to_pos_besteffort(
        self, window: WindowHyprland, pos: tuple[int, int]
    ) -> None:
        if (pos_curr := window.get_pos()) == pos:
            logger.warning(
                f"geometry/hyprland> [{window}] already at {pos}, skipping..."
            )
            return

        logger.info(f"geometry/hyprland> [{window}] -> {pos}...")
        for __ in range(5):
            logger.info(
                f"geometry/hyprland> rotating [{window}]: current pos {pos_curr}"
            )
            talk.HyprTalk("swapprev").execute_as_layoutmsg()
            if (pos_curr := window.get_pos()) == pos:
                logger.info(f"geometry/hyprland> arrived at target {pos}, done!")
                return


class ManagementHyprland(libwm.Management):
    def __init__(self):
        super().__init__()
        self._monitors_workspace_current = []
        self._hold: HoldHyprland = None  # type: ignore [annotation-unchecked]

    @property
    def hold(self) -> HoldHyprland:
        return self._hold

    def load_monitors(self) -> None:
        for j in talk.HyprTalk("monitors").execute_to_json():
            self._monitors.append(
                MonitorHyprland(
                    identifier=j["id"],
                    name=j["name"],
                    #
                    size_x=j["width"],
                    size_y=j["height"],
                )
            )
            self._monitors_workspace_current.append(j["activeWorkspace"]["id"])

    def load_workspaces(self) -> None:
        for j in WorkspaceHyprland.jsons():
            if HoldHyprland.is_hold(j["name"]):
                self._hold = HoldHyprland.from_json(j)
                continue

            workspace = WorkspaceHyprland.from_json(j)
            self._workspaces.append(workspace)

            identifier = j["id"]
            if identifier in self._monitors_workspace_current:
                self._monitors[
                    self._monitors_workspace_current.index(identifier)
                ].set_current(workspace)

            monitor = self.monitor_find(j["monitorID"])
            monitor.workspaces().append(workspace)
            logging.debug(f"({monitor}) += ({workspace})")

    def load_windows(self) -> None:
        for j in WindowHyprland.jsons_by_time():
            window = WindowHyprland.from_json(j)
            self._windows.append(window)

            if HoldHyprland.is_hold(j["workspace"]["name"]):
                logging.debug(f"({self._hold}) += ({window})")
                self._hold.windows().append(window)
                continue

            workspace = self.workspace_find(j["workspace"]["id"])
            logging.debug(f"({workspace}) += ({window})")
            workspace.windows().append(window)

    def _workspace_new(self, workspace: typing.Any) -> None:
        # TODO:
        #   fetch new workspace
        #   append this new workspace to self._workspaces
        WorkspaceHyprland.goto_new(workspace)

    def _workspace_new_add_window(
        self, workspace: typing.Any, window: WindowHyprland
    ) -> None:
        WorkspaceHyprland.add_new(workspace, window)

    def workspace_current(self) -> WorkspaceHyprland:
        return self.workspace_find(WorkspaceHyprland.json_current()["id"])

    def _window_from_format_human(self, format_human: typing.Any) -> WindowHyprland:
        for window in self._windows:
            if window == WindowHyprland.identifier_from_format_human(format_human):
                return window
        raise libwm.WindowError

    def window_is_onhold(self, window: WindowHyprland) -> bool:
        return self._hold and self._hold.has(window)

    def window_prev_nonhold(self) -> None:
        windows = iter(self._windows)
        if not self.hold_is_active():
            try:
                next(windows)
            except StopIteration as e:
                raise libwm.WindowError(
                    "libhyprland> no previous window (exists only one window)"
                ) from e

        for window in windows:
            if not self.window_is_onhold(window):
                return window
        raise libwm.WindowError("libhyprland> no previous non-hold window")

    def hold_is_active(self) -> bool:
        return HoldHyprland.is_hold(WindowHyprland.json_current()["workspace"]["name"])

    def hold_peek(self) -> None:
        if not self._hold:
            logger.warning("libhyprland> hold does not exist yet")
            HoldHyprland.toggle()
            WindowHyprland.from_footclient().group_toggle()
            return

        if self._hold.is_empty():
            logger.warning("libhyprland> hold is empty")
            HoldHyprland.show()
            WindowHyprland.from_footclient().group_toggle()
            return

        HoldHyprland.show()

    def hold_add(self, window: WindowHyprland) -> None:
        if not self._hold:
            HoldHyprland.add_new(window)
            return
        if self._hold.has(window):
            logger.warning(f"libhyprland> [{window}] already on hold; skipping...")
            return
        self._hold.add(window)

    def hold_split(self, window: WindowHyprland) -> WindowHyprland:
        if not self._hold:
            raise libwm.WorkspaceError("libhyprland> hold does not exist yet")
        if not self._hold.has(window):
            raise libwm.WorkspaceError(f"libhyprland> [{window}] not on hold")
        return self._hold.split(window)

    def hold_choose_windows(self) -> cabc.Iterable[WindowHyprland]:
        if not self._hold:
            logger.warning("libhyprland> hold does not exist yet")
            return
        if self._hold.is_empty():
            logger.warning("libhyprland> hold is empty")
            return
        yield from self.choose_windows(self._hold.windows())

    def hold_choose_window(self) -> WindowHyprland:
        if not self._hold:
            raise libwm.WorkspaceError("libhyprland> hold does not exist yet")
        if self._hold.is_empty():
            raise libwm.WorkspaceError("libhyprland> hold is empty")
        return self.choose_window(self._hold.windows())
