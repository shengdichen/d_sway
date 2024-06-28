import collections.abc as cabc
import typing

from talk import HyprTalk


class HyprMonitor:
    def __init__(
        self,
        _id: int,
        name: str,
        description: str,
        make: str,
        model: str,
        serial: str,
        width: int,
        height: int,
        refresh_rate: float,
        x: int,
        y: int,
        active_workspace_id: int,
        active_workspace_name: str,
        special_workspace_id: int,
        special_workspace_name: str,
        reserved: list,
        scale: float,
        transform: int,
        focused: bool,
        dpms_status: bool,
        vrr: bool,
        actively_tearing: bool,
        disabled: bool,
        current_format: str,
        available_modes: list[str],
    ):  # pylint: disable=too-many-locals
        self._id = _id
        self._name = name
        self._description = description
        self._make = make
        self._model = model
        self._serial = serial
        self._width = width
        self._height = height
        self._refresh_rate = refresh_rate
        self._x = x
        self._y = y
        self._active_workspace_id = active_workspace_id
        self._active_workspace_name = active_workspace_name
        self._special_workspace_id = special_workspace_id
        self._special_workspace_name = special_workspace_name
        self._reserved = reserved
        self._scale = scale
        self._transform = transform
        self._focused = focused
        self._dpms_status = dpms_status
        self._vrr = vrr
        self._actively_tearing = actively_tearing
        self._disabled = disabled
        self._current_format = current_format
        self._available_modes = available_modes

    @classmethod
    def from_json(cls, js: dict) -> "HyprMonitor":
        return cls(
            _id=js["id"],
            name=js["name"],
            description=js["description"],
            make=js["make"],
            model=js["model"],
            serial=js["serial"],
            width=js["width"],
            height=js["height"],
            refresh_rate=js["refreshRate"],
            x=js["x"],
            y=js["y"],
            active_workspace_id=js["activeWorkspace"]["id"],
            active_workspace_name=js["activeWorkspace"]["name"],
            special_workspace_id=js["specialWorkspace"]["id"],
            special_workspace_name=js["specialWorkspace"]["name"],
            reserved=js["reserved"],
            scale=js["scale"],
            transform=js["transform"],
            focused=js["focused"],
            dpms_status=js["dpmsStatus"],
            vrr=js["vrr"],
            actively_tearing=js["activelyTearing"],
            disabled=js["disabled"],
            current_format=js["currentFormat"],
            available_modes=js["availableModes"],
        )

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @classmethod
    def monitors(cls) -> cabc.Generator["HyprMonitor", None, None]:
        for js in cls.monitors_json():
            yield cls.from_json(js)

    @staticmethod
    def monitors_json() -> cabc.Sequence[dict]:
        return HyprTalk("monitors").execute_to_json()

    @classmethod
    def from_id(cls, _id: int) -> "HyprMonitor":
        for js in cls.monitors_json():
            if js["id"] == _id:
                return cls.from_json(js)
        raise RuntimeError(f"monitor> monitor not found [id: {_id}]")

    @classmethod
    def from_name(cls, name: str) -> "HyprMonitor":
        for js in cls.monitors_json():
            if js["name"] == name:
                return cls.from_json(js)
        raise RuntimeError(f"monitor> monitor not found [name: {name}]")

    @classmethod
    def from_current(cls) -> "HyprMonitor":
        return HyprWorkspace.from_current().monitor

    def print(self) -> None:
        print(f"monitor> {self._id}.{self._name}")


class HyprWorkspace:
    def __init__(
        self,
        _id: int,
        name: str,
        n_windows: int,
        has_fullscreen: bool,
        last_active_window_id: str,
        last_active_window_title: str,
        monitor: HyprMonitor,
    ):
        self._id = _id
        self._name = name
        self._n_windows = n_windows
        self._has_fullscreen = has_fullscreen
        self._last_active_window_id = last_active_window_id
        self._last_active_window_title = last_active_window_title

        self._monitor = monitor

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def n_windows(self) -> int:
        return self._n_windows

    @property
    def monitor(self) -> HyprMonitor:
        return self._monitor

    @classmethod
    def from_json(cls, j: dict) -> "HyprWorkspace":
        return cls(
            _id=j["id"],
            name=j["name"],
            n_windows=j["windows"],
            has_fullscreen=j["hasfullscreen"],
            last_active_window_id=j["lastwindow"],
            last_active_window_title=j["lastwindowtitle"],
            monitor=HyprMonitor.from_name(j["monitor"]),
        )

    @classmethod
    def from_current(cls) -> "HyprWorkspace":
        return cls.from_json(HyprTalk("activeworkspace").execute_to_json())

    @classmethod
    def from_id(cls, _id: int) -> "HyprWorkspace":
        for j in cls.workspaces_json():
            if j["id"] == _id:
                return cls.from_json(j)
        raise ValueError(f"workspace> workspace not found [id: {_id}]")

    @classmethod
    def from_name(cls, name: str) -> "HyprWorkspace":
        for j in cls.workspaces_json():
            if j["name"] == name:
                return cls.from_json(j)
        raise ValueError(f"workspace> workspace not found [name: {name}]")

    @classmethod
    def from_name_special(cls, name: str) -> "HyprWorkspace":
        return cls.from_name(cls.name_from_special(name))

    @classmethod
    def from_hold(cls) -> "HyprWorkspace":
        return cls.from_name_special("HOLD")

    @staticmethod
    def name_from_special(name: str) -> str:
        return f"special:{name}"

    @staticmethod
    def name_hold() -> str:
        return HyprWorkspace.name_from_special("HOLD")

    @classmethod
    def workspaces(cls) -> cabc.Generator["HyprWorkspace", None, None]:
        for j in cls.workspaces_json():
            yield cls.from_json(j)

    @staticmethod
    def workspaces_json() -> cabc.Sequence[dict]:
        return HyprTalk("workspaces").execute_to_json()

    def is_workspace_hold(self) -> bool:
        return self._name == "special:HOLD"

    def is_empty(self) -> bool:
        return HyprWorkspace.from_current().n_windows == 0

    def print(self) -> None:
        print(
            f'workspace> ({self._id}."{self._name}"): -> '
            f"({self._last_active_window_id}: {self._last_active_window_title})"
        )



class HyprWindow:  # pylint: disable=too-many-public-methods
    def __init__(
        self,
        address: int,
        mapped: bool,
        hidden: bool,
        _at: tuple[int, int],
        _size: tuple[int, int],
        floating: bool,
        _class: str,
        title: str,
        class_initial: str,
        title_initial: str,
        pid: int,
        xwayland: bool,
        pinned: bool,
        is_fullscreen: bool,
        fullscreen_mode: int,
        fake_fullscreen: bool,
        grouped: list,
        swallowing: str,
        idx_focus: int,
        workspace: HyprWorkspace,
        monitor: HyprMonitor,
    ):  # pylint: disable=too-many-locals
        self._address = address
        self._mapped = mapped
        self._hidden = hidden
        self._at = _at
        self._size = _size

        self._floating = floating
        self._class = _class
        self._title = title
        self._class_initial = class_initial
        self._title_initial = title_initial
        self._pid = pid
        self._xwayland = xwayland
        self._pinned = pinned
        self._is_fullscreen = is_fullscreen
        self._fullscreen_mode = fullscreen_mode
        self._fake_fullscreen = fake_fullscreen
        self._grouped = grouped
        self._swallowing = swallowing
        self._idx_focus = idx_focus

        self._workspace = workspace
        self._monitor = monitor

    @property
    def address(self) -> int:
        return self._address

    @property
    def workspace(self) -> HyprWorkspace:
        return self._workspace

    @property
    def is_fullscreen(self) -> bool:
        return self._is_fullscreen

    @property
    def idx_focus(self) -> int:
        return self._idx_focus

    @classmethod
    def from_json(cls, j: dict) -> "HyprWindow":
        return cls(
            address=j["address"],
            mapped=j["mapped"],
            hidden=j["hidden"],
            _at=j["at"],
            _size=j["size"],
            floating=j["floating"],
            _class=j["class"],
            title=j["title"],
            class_initial=j["initialClass"],
            title_initial=j["initialTitle"],
            pid=j["pid"],
            xwayland=j["xwayland"],
            pinned=j["pinned"],
            is_fullscreen=j["fullscreen"],
            fullscreen_mode=j["fullscreenMode"],
            fake_fullscreen=j["fakeFullscreen"],
            grouped=j["grouped"],
            swallowing=j["swallowing"],
            idx_focus=j["focusHistoryID"],
            workspace=HyprWorkspace.from_id(j["workspace"]["id"]),
            monitor=HyprMonitor.from_id(j["monitor"]),
        )

    @classmethod
    def windows(
        cls, sort_by_focus: bool = True
    ) -> cabc.Generator["HyprWindow", None, None]:
        for j in cls.windows_json(sort_by_focus=sort_by_focus):
            yield cls.from_json(j)

    @staticmethod
    def windows_json(sort_by_focus: bool = True) -> cabc.Sequence[dict]:
        jsons = HyprTalk("clients").execute_to_json()
        if not sort_by_focus:
            return jsons
        return sorted(jsons, key=lambda j: j["focusHistoryID"])

    @classmethod
    def from_current(cls) -> "HyprWindow":
        return cls.from_json(HyprTalk("activewindow").execute_to_json())

    @classmethod
    def from_address(cls, address: int) -> "HyprWindow":
        for j in cls.windows_json():
            if j["address"] == address:
                return cls.from_json(j)
        raise ValueError(f"window> window not found [address: {address}]")

    def print(self) -> None:
        print(
            f"window> {self._address}: {self._title} "
            f"[focus: {self._idx_focus}, "
            f"monitor: {self._monitor.id}.{self._monitor.name}]"
        )

    @classmethod
    def from_previous(
        cls,
        monitor_current: bool = False,
    ) -> "HyprWindow":
        windows = cls.windows(sort_by_focus=True)
        next(windows)  # pop the first (current) window

        if not monitor_current:
            return next(windows)

        mid = HyprMonitor.from_current().id
        for window in windows:
            if window.is_on_monitor(mid):
                return window

        raise RuntimeError("window> no previous window")

    def is_on_monitor(self, monitor_id: int) -> bool:
        return self._monitor.id == monitor_id

    def move_window_to_workspace(
        self,
        workspace: HyprWorkspace | str,
        silent: bool = False,
    ) -> None:
        # workspace could be non-existing (empty) before moving
        if isinstance(workspace, HyprWorkspace):
            workspace = workspace.name
        cmd = "movetoworkspacesilent" if silent else "movetoworkspace"
        cmd = f"{cmd} {workspace},address:{self._address}"
        HyprTalk(cmd).execute_as_dispatch()

    def group_on_toggle(self) -> None:
        if self.is_grouped():
            return

        HyprWindow.focus(self)  # must focus before grouping
        HyprTalk("togglegroup").execute_as_dispatch()

    def group_on_move(self) -> None:
        if self.is_grouped():
            return

        HyprWindow.focus(self)  # must focus before grouping
        addr = self._address
        for d in "lrud":
            HyprTalk(f"moveintogroup {d}").execute_as_dispatch()
            if HyprWindow.from_address(addr).is_grouped():
                return
        raise RuntimeError(f"group> still not in group [{self._title}]")

    def group_off_toggle(self) -> None:
        if not self.is_grouped():
            return

        HyprWindow.focus(self)  # must focus before grouping
        HyprTalk("togglegroup").execute_as_dispatch()

    def group_off_move(self) -> None:
        if not self.is_grouped():
            return

        HyprTalk(f"moveoutofgroup address:{self._address}").execute_as_dispatch()

    def is_grouped(self) -> bool:
        if not self._grouped:
            return False
        return True

    @staticmethod
    def focus(window: "HyprWindow") -> None:
        HyprTalk(f"focuswindow address:{window.address}").execute_as_dispatch()

    def move_to_current(self, silent: bool = True) -> None:
        self.move_window_to_workspace(HyprWorkspace.from_current(), silent=silent)
        HyprWindow.focus(self)

    @staticmethod
    def fullscreen_on() -> None:
        if not HyprWindow.from_current().is_fullscreen:
            HyprTalk("fullscreen").execute_as_dispatch()

    @staticmethod
    def fullscreen_off() -> None:
        if HyprWindow.from_current().is_fullscreen:
            HyprTalk("fullscreen").execute_as_dispatch()

    def selection_prompt(self) -> str:
        return f"{self._title} [ADDR: {self._address}]"


class Launch:
    def __init__(self, cmd: str):
        self._cmd = cmd

    def launch(self, rules: typing.Optional[cabc.Sequence[str]] = None) -> None:
        cmd = "exec"
        if rules:
            cmd = f"{cmd} [{','.join(rules)}]"
        cmd = f"{cmd} {self._cmd}"
        HyprTalk(cmd).execute_as_dispatch()

    @staticmethod
    def launch_foot(cmd_extra: str = "", as_float: bool = True) -> None:
        cmd = "foot"
        if cmd_extra:
            cmd = f"{cmd} {cmd_extra}"

        if as_float:
            Launch(cmd).launch(["float"])
        else:
            Launch(cmd).launch()
