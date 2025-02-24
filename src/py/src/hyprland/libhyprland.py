import collections.abc as cabc
import logging
import re
import time
import typing

from common import libwm, prettyprint
from hyprland import launch, talk

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
        if j := WindowHyprland.json_current():
            return cls.from_json(j)
        raise libwm.WindowError

    @staticmethod
    def jsons() -> list[dict]:
        return talk.HyprTalk("clients").execute_to_json()

    @staticmethod
    def jsons_by_time() -> cabc.Generator[dict, None, None]:
        yield from sorted(WindowHyprland.jsons(), key=lambda _j: _j["focusHistoryID"])

    @staticmethod
    def json_current() -> dict:
        # will return the empty dict when not focused on any window: for example, after the last
        # window of current workspace is closed
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

    def opacity_toggle(self) -> None:
        logger.debug(f"window/hyprland> opacity-toggle [{self}]")
        cmd = f"{self.as_addr()} opaque toggle"
        talk.HyprTalk(cmd).execute_as_setprop()

    def fullscreen_toggle(self) -> None:
        logger.debug(f"window/hyprland> fullscreen-toggle [{self}]")
        talk.HyprTalk("fullscreen 1").execute_as_dispatch()

    def fullscreen_toggle_nodecoration(self) -> None:
        logger.debug(f"window/hyprland> fullscreen-toggle, no-decoration [{self}]")
        talk.HyprTalk("fullscreen 0").execute_as_dispatch()


class WorkspaceHyprland(libwm.Workspace):
    def __init__(self, name: str = "", identifier: int = 0):
        super().__init__(identifier=identifier)
        self._name = name

    @property
    def identifier(self) -> int:
        return self._identifier

    @identifier.setter
    def identifier(self, value: int) -> None:
        self._identifier = value

    def exists(self) -> bool:
        return bool(self._name)

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, str):
            return self._name == that
        if isinstance(that, int):
            return self._identifier == that
        return super().__eq__(that)

    @classmethod
    def from_json(cls, j: dict) -> "WorkspaceHyprland":
        return cls(identifier=j["id"], name=j["name"])

    @classmethod
    def from_new(cls, name: str) -> "WorkspaceHyprland":
        return cls(name=name)

    @staticmethod
    def name_is_special(name: str) -> bool:
        return name.startswith("special:")

    @staticmethod
    def jsons() -> cabc.Sequence[dict]:
        return talk.HyprTalk("workspaces").execute_to_json()

    def _add(self, window: WindowHyprland) -> None:
        logger.info(f"workspace/hyprland> [{self}]: adding [{window}]")
        cmd = f"movetoworkspace {self._name},{window.as_addr()}"
        talk.HyprTalk(cmd).execute_as_dispatch()

    @staticmethod
    def add_new(workspace: typing.Any, window: WindowHyprland) -> None:
        logger.info(f"workspace/hyprland> new [{workspace}]: adding [{window}]")
        cmd = f"movetoworkspace {workspace},{window.as_addr()}"
        talk.HyprTalk(cmd).execute_as_dispatch()
        WindowHyprland.from_footclient()

    def goto(self) -> None:
        logger.debug(f"workspace/hyprland> goto [{self}]")
        cmd = f"workspace {self._name}"
        talk.HyprTalk(cmd).execute_as_dispatch()

    @staticmethod
    def goto_new(workspace: typing.Any) -> None:
        logger.debug(f"workspace/hyprland> goto-new [{workspace}]")
        cmd = f"workspace {workspace}"
        talk.HyprTalk(cmd).execute_as_dispatch()
        WindowHyprland.from_footclient()


class WorkspaceHyprlandNormal(WorkspaceHyprland):
    def __str__(self) -> str:
        return (
            "workspace/hyprland-normal> "
            f"{self._identifier}.'{self._name}', size {len(self._windows)}"
        )

    @staticmethod
    def json_current() -> dict:
        # NOTE:
        #   |activeworkspace| considers only non-special workspaces: if on special
        #   workspace, will return the non-special workspace in background
        # NOTE:
        #   to also consider special workspaces, use |activewindow| and access
        #   ["workspace"]["id" OR "name"] if |activewindow| returns non-empty dict, i.e.,
        #   has currently focused window; otherwise the logic is much more complicated: see
        #   |ManagementHyprland| for implementation
        # NOTE:
        #   this is guaranteed to be always valid (non-empty) even if no window exists
        #   (on current workspace or even globally)
        return talk.HyprTalk("activeworkspace").execute_to_json()


class WorkspaceHyprlandSpecial(WorkspaceHyprland):
    def __init__(self, name: str = "", identifier: int = 0):
        super().__init__(name=name, identifier=identifier)
        self._name_pure = self._name[8:]  # without the leading |special:|

    def __str__(self) -> str:
        return (
            "workspace/hyprland-special> "
            f"{self._identifier}.'{self._name_pure}', size {len(self._windows)}"
        )

    def show(self) -> None:
        monitor_id = WorkspaceHyprlandNormal.json_current()["monitorID"]

        for j in talk.HyprTalk("monitors").execute_to_json():
            if j["specialWorkspace"]["name"] != self._name:
                continue
            if j["id"] == monitor_id:
                logger.warning(
                    f"workspace/hyprland-special> showing [{self}] already, skipping..."
                )
                return
            logger.info(
                f"workspace/hyprland-special> [{self}] currently on monitor [{j['id']}]"
                f", now showing on monitor [{monitor_id}]"
            )
            self.toggle()
            return

        logger.info(
            f"workspace/hyprland-special> showing [{self}] for monitor [{monitor_id}]"
        )
        self.toggle()

    def hide(self) -> None:
        monitor_id = WorkspaceHyprlandNormal.json_current()["monitorID"]

        for j in talk.HyprTalk("monitors").execute_to_json():
            if j["specialWorkspace"]["name"] != self._name:
                continue
            if j["id"] == monitor_id:
                logger.info(
                    f"workspace/hyprland-special> [{self}] on current monitor [{monitor_id}]"
                    ", toggling once to turn off"
                )
                self.toggle()
                return
            logger.info(
                f"workspace/hyprland-special> [{self}] currently on another monitor [{j['id']}]"
                ", toggling twice to turn off"
            )
            self.toggle()  # make visible on current monitor...
            self.toggle()  # ...then turn off
            return

        logger.warning(f"workspace/hyprland-special> [{self}] off already, skipping...")

    def toggle(self) -> None:
        logger.info(f"workspace/hyprland-special> toggling [{self}]")
        talk.HyprTalk(f"togglespecialworkspace {self._name_pure}").execute_as_dispatch()


class HoldHyprland(WorkspaceHyprlandSpecial):
    NAME_FULL = "special:HOLD"

    def __init__(self, identifier: int = 0):
        super().__init__(name=HoldHyprland.NAME_FULL, identifier=identifier)

    def __str__(self) -> str:
        return f"hold/hyprland> size {len(self._windows)} [id: {self._identifier}]"

    @staticmethod
    def is_hold(name: str) -> bool:
        return HoldHyprland.NAME_FULL == name

    def _add(self, window: WindowHyprland) -> None:
        logger.info(f"hold/hyprland> adding [{window}]")
        super()._add(window)
        window.group_join()

    def split(self, window: WindowHyprland) -> WindowHyprland:
        logger.info(f"hold/hyprland> splitting [{window}]")
        window.group_leave()
        self._windows.remove(window)
        return window


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
        self._hold = HoldHyprland()

        self._monitors_workspace_current = []
        self._monitor_to_workspaces: dict[int, tuple[str, str]] = {}

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
            self._monitor_to_workspaces[j["id"]] = (
                j["activeWorkspace"]["name"],
                j["specialWorkspace"]["name"],
            )
            self._monitors_workspace_current.append(j["activeWorkspace"]["id"])

        logger.debug(
            "libhyprland/load-monitors> "
            "monitor->(workspace-nonspecial, workspace-special): "
            f"{self._monitor_to_workspaces}"
        )

    def load_workspaces(self) -> None:
        for j in WorkspaceHyprland.jsons():
            if j["name"] == self._hold:
                self._hold.identifier = j["id"]
                continue

            if not WorkspaceHyprland.name_is_special(j["name"]):
                workspace = WorkspaceHyprlandNormal.from_json(j)
            else:
                workspace = WorkspaceHyprlandSpecial.from_json(j)
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

            if j["workspace"]["name"] == self._hold:
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
        logger.info(f"libhyprland/workspace-new> [{workspace}]")
        WorkspaceHyprland.from_new(workspace).goto()
        WindowHyprland.from_footclient()

    def _workspace_new_add_window(
        self, workspace: typing.Any, window: WindowHyprland
    ) -> None:
        WorkspaceHyprland.from_new(workspace).add(window)

    def workspace_current(self) -> WorkspaceHyprland:
        w = WorkspaceHyprlandNormal.json_current()["name"]
        for workspace_normal, workspace_special in self._monitor_to_workspaces.values():
            if workspace_normal != w:
                continue
            if not workspace_special:
                workspace = self.workspace_find(workspace_normal)
                logger.info(
                    "libhyprland/workspace-current> monitor showing "
                    f"only normal [{workspace_normal}]"
                )
                return workspace
            if workspace_special == self._hold:
                workspace = self.workspace_find(workspace_normal)
                logger.info(
                    f"libhyprland/workspace-current> monitor showing "
                    f"normal [{workspace_normal}] AND [{HoldHyprland.NAME_FULL}]; "
                    f"ignoring HOLD and using normal [{workspace_normal}]"
                )
                return workspace
            workspace = self.workspace_find(workspace_special)
            logger.info(
                "libhyprland/workspace-current> monitor showing "
                f"normal [{workspace_normal}] AND [{workspace_special}]; "
                f"preferring special [{workspace}]"
            )
            return workspace
        logger.error(
            "libhyprland/workspace-current> non found: something is seriously wrong..."
        )
        raise libwm.WorkspaceError  # this should never happen

    def workspace_current_nonspecial(self) -> WorkspaceHyprlandNormal:
        return self.workspace_find(WorkspaceHyprlandNormal.json_current()["id"])

    def _window_from_format_human(self, format_human: typing.Any) -> WindowHyprland:
        for window in self._windows:
            if window == WindowHyprland.identifier_from_format_human(format_human):
                return window
        raise libwm.WindowError

    def window_is_onhold(self, window: WindowHyprland) -> bool:
        return self._hold.has(window)

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
        for __, workspace_special in self._monitor_to_workspaces.values():
            if workspace_special == self._hold:
                return True
        return False

    def hold_peek(self) -> None:
        if not self._hold.exists():
            logger.warning("libhyprland> hold does not exist yet")
            self._hold.toggle()
            WindowHyprland.from_footclient().group_toggle()
            return

        if self._hold.is_empty():
            logger.warning("libhyprland> hold is empty")
            self._hold.show()
            WindowHyprland.from_footclient().group_toggle()
            return

        self._hold.show()

    def hold_add(self, window: WindowHyprland) -> None:
        if not self._hold.exists():
            self._hold.add(window)
            return
        if self._hold.has(window):
            logger.warning(f"libhyprland> [{window}] already on hold; skipping...")
            return
        self._hold.add(window)

    def hold_split(self, window: WindowHyprland) -> WindowHyprland:
        if not self._hold.exists():
            raise libwm.WorkspaceError("libhyprland> hold does not exist yet")
        if not self._hold.has(window):
            raise libwm.WorkspaceError(f"libhyprland> [{window}] not on hold")
        return self._hold.split(window)

    def hold_choose_windows(self) -> cabc.Iterable[WindowHyprland]:
        if not self._hold.exists():
            logger.warning("libhyprland> hold does not exist yet")
            return
        if self._hold.is_empty():
            logger.warning("libhyprland> hold is empty")
            return
        yield from self.choose_windows(self._hold.windows())

    def hold_choose_window(self) -> WindowHyprland:
        if not self._hold.exists():
            raise libwm.WorkspaceError("libhyprland> hold does not exist yet")
        if self._hold.is_empty():
            raise libwm.WorkspaceError("libhyprland> hold is empty")
        return self.choose_window(self._hold.windows())
