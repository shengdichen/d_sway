import collections.abc as cabc
import re
import typing

import prettyprint
import talk


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

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, int):
            return self._id == that
        if isinstance(that, str):
            return self._name == that
        if isinstance(that, HyprMonitor):
            return self._id == that.id
        return False

    @classmethod
    def monitors(cls) -> cabc.Generator["HyprMonitor", None, None]:
        for js in cls.monitors_json():
            yield cls.from_json(js)

    @staticmethod
    def monitors_json() -> cabc.Sequence[dict]:
        return talk.HyprTalk("monitors").execute_to_json()

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

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, int):
            return self._id == that
        if isinstance(that, str):
            return self._name == that
        if isinstance(that, HyprWorkspace):
            return self._id == that.id
        return False

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
        return cls.from_json(talk.HyprTalk("activeworkspace").execute_to_json())

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

    @staticmethod
    def name_from_special(name: str) -> str:
        return f"special:{name}"

    @classmethod
    def workspaces(cls) -> cabc.Generator["HyprWorkspace", None, None]:
        for j in cls.workspaces_json():
            yield cls.from_json(j)

    @staticmethod
    def workspaces_json() -> cabc.Sequence[dict]:
        return talk.HyprTalk("workspaces").execute_to_json()

    def print(self) -> None:
        print(
            f'workspace> ({self._id}."{self._name}"): -> '
            f"({self._last_active_window_id}: {self._last_active_window_title})"
        )

    def windows(self) -> cabc.Generator["HyprWindow", None, None]:
        yield from HyprWindow.windows(workspace=self)

    @staticmethod
    def focus_master() -> None:
        return talk.HyprTalk("focusmaster master").execute_as_layoutmsg()

    @staticmethod
    def window_master() -> "HyprWindow":
        HyprWorkspace.focus_master()
        return HyprWindow.from_current()

    def is_special(self) -> bool:
        return self._name.startswith("special:")

    def is_empty(self) -> bool:
        return self._n_windows == 0

    @staticmethod
    def focus(workspace: typing.Union[str, "HyprWorkspace"]) -> None:
        if isinstance(workspace, HyprWorkspace):
            workspace = workspace.name
        talk.HyprTalk(f"workspace {workspace}").execute_as_dispatch()


class HyprWindow:  # pylint: disable=too-many-public-methods
    PATTERN_SELECTION_PROMPT = re.compile(r"^.* (0x[0-9a-f]*)$")

    def __init__(
        self,
        address: str,  # str-repr of hex-int
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
        fullscreen_mode_internal: bool,
        fullscreen_mode_client: int,
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

        self._fullscreen_mode_internal = fullscreen_mode_internal
        self._fullscreen_mode_client = fullscreen_mode_client

        self._grouped = grouped
        self._swallowing = swallowing
        self._idx_focus = idx_focus

        self._workspace = workspace
        self._monitor = monitor

    @property
    def address(self) -> str:
        return self._address

    @property
    def is_fullscreen(self) -> bool:
        return self._fullscreen_mode_internal != 0

    @property
    def is_fullscreen_with_decoration(self) -> bool:
        return self._fullscreen_mode_internal == 1

    @property
    def is_fullscreen_without_decoration(self) -> bool:
        return self._fullscreen_mode_internal == 2

    @property
    def idx_focus(self) -> int:
        return self._idx_focus

    @property
    def workspace(self) -> HyprWorkspace:
        return self._workspace

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, int):
            return self._address == that
        if isinstance(that, HyprWindow):
            return self._address == that.address
        return False

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
            fullscreen_mode_internal=j["fullscreen"],
            fullscreen_mode_client=j["fullscreenClient"],
            grouped=j["grouped"],
            swallowing=j["swallowing"],
            idx_focus=j["focusHistoryID"],
            workspace=HyprWorkspace.from_id(j["workspace"]["id"]),
            monitor=HyprMonitor.from_id(j["monitor"]),
        )

    @classmethod
    def windows(
        cls,
        workspace: typing.Optional[HyprWorkspace] = None,
        sort_by_focus: bool = True,
    ) -> cabc.Generator["HyprWindow", None, None]:
        if workspace:
            wid = workspace.id
            for j in cls.windows_json(sort_by_focus=sort_by_focus):
                if j["workspace"]["id"] == wid:
                    yield cls.from_json(j)
        else:
            for j in cls.windows_json(sort_by_focus=sort_by_focus):
                yield cls.from_json(j)

    @staticmethod
    def windows_json(sort_by_focus: bool = True) -> cabc.Sequence[dict]:
        jsons = talk.HyprTalk("clients").execute_to_json()
        if not sort_by_focus:
            return jsons
        return sorted(jsons, key=lambda j: j["focusHistoryID"])

    def opacity_toggle(self) -> None:
        cmd = f"address:{self._address} opaque toggle"
        talk.HyprTalk(cmd).execute_as_setprop()

    @classmethod
    def from_current(
        cls, workspace: typing.Optional[HyprWorkspace] = None
    ) -> "HyprWindow":
        if not workspace:
            return cls.from_json(talk.HyprTalk("activewindow").execute_to_json())

        workspace_id = workspace.id
        for j in cls.windows_json():
            if j["workspace"]["id"] == workspace_id:
                return cls.from_json(j)
        raise RuntimeError(f"window> window not found [workspace: {workspace.id}]")

    @classmethod
    def from_address(cls, address: str) -> "HyprWindow":
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

        monitor = HyprMonitor.from_current()
        for window in windows:
            if window.is_on_monitor(monitor):
                return window

        raise RuntimeError("window> no previous window")

    @classmethod
    def from_previous_in_workspace(cls, workspace: HyprWorkspace) -> "HyprWindow":
        try:
            return next(cls.windows(workspace=workspace, sort_by_focus=True))
        except StopIteration as e:
            raise RuntimeError(
                f"window> no previous window [workspace: {workspace.name}]"
            ) from e

    @classmethod
    def from_previous_relative(
        cls,
        relative_to: typing.Optional["HyprWindow"] = None,
    ) -> "HyprWindow":
        relative_to = relative_to or cls.from_current()
        idx_focus = relative_to.idx_focus + 1
        for window in cls.windows(sort_by_focus=True):
            if window.idx_focus == idx_focus:
                return window
        raise RuntimeError("window> no previous window")

    @classmethod
    def from_selection_prompt(cls, choice: str) -> "HyprWindow":
        m = cls.PATTERN_SELECTION_PROMPT.match(choice)
        if not m:
            raise RuntimeError(f"window> invalid choice {choice}")
        return cls.from_address(m.group(1))

    def is_on_monitor(self, monitor: typing.Any) -> bool:
        return self._monitor == monitor

    def is_in_workspace(self, workspace: typing.Any) -> bool:
        return self._workspace == workspace

    def is_in_workspace_special(self) -> bool:
        return self._workspace.is_special()

    def move_to_workspace(
        self,
        workspace: HyprWorkspace | str,
        silent: bool = False,
    ) -> None:
        # workspace could be non-existing (empty) before moving
        if isinstance(workspace, HyprWorkspace):
            workspace = workspace.name
        cmd = "movetoworkspacesilent" if silent else "movetoworkspace"
        cmd = f"{cmd} {workspace},address:{self._address}"
        talk.HyprTalk(cmd).execute_as_dispatch()

    def group_on_toggle(self) -> None:
        if self.is_grouped():
            return

        self.focus()  # must focus before grouping
        talk.HyprTalk("togglegroup").execute_as_dispatch()

    def group_on_move(self) -> None:
        if self.is_grouped():
            return

        self.focus()  # must focus before grouping
        addr = self._address
        for d in "lrud":
            talk.HyprTalk(f"moveintogroup {d}").execute_as_dispatch()
            if HyprWindow.from_address(addr).is_grouped():
                return
        raise RuntimeError(f"group> still not in group [{self._title}]")

    def group_off_toggle(self) -> None:
        if not self.is_grouped():
            return

        self.focus()  # must focus before grouping
        talk.HyprTalk("togglegroup").execute_as_dispatch()

    def group_off_move(self) -> None:
        if not self.is_grouped():
            return

        talk.HyprTalk(f"moveoutofgroup address:{self._address}").execute_as_dispatch()

    def is_grouped(self) -> bool:
        if not self._grouped:
            return False
        return True

    def focus(self) -> None:
        talk.HyprTalk(f"focuswindow address:{self._address}").execute_as_dispatch()

    def move_to_current(self) -> None:
        self.move_to_workspace(HyprWorkspace.from_current())

    def fullscreen_on(self, keep_decoration: bool = True) -> None:
        if self.is_fullscreen:
            return
        HyprWindow.fullscreen_toggle(keep_decoration_when_fullscreen=keep_decoration)

    def fullscreen_off(self) -> None:
        if not self.is_fullscreen:
            return

        if self.is_fullscreen_with_decoration:
            HyprWindow.fullscreen_toggle()
            return

        # fullscreen without decoration
        HyprWindow.fullscreen_toggle(keep_decoration_when_fullscreen=False)

    def fullscreen(self) -> None:
        if self.is_fullscreen:
            self.fullscreen_off()
            return
        self.fullscreen_on()

    def fullscreen_mode_switch(self, guarantee_fullscreen: bool = True) -> None:
        # not fullscreen -> fullscreen no-deco
        if not self.is_fullscreen and guarantee_fullscreen:
            self.fullscreen_on(keep_decoration=False)
            return

        # fullscreen with deco -> fullscreen no-deco
        if self.is_fullscreen_with_decoration:
            HyprWindow.fullscreen_toggle(keep_decoration_when_fullscreen=False)
            return

        # fullscreen no-deco -> fullscreen with deco
        HyprWindow.fullscreen_toggle()

    def fullscreen_cycle(self) -> None:
        if not self.is_fullscreen:
            HyprWindow.fullscreen_toggle()
            return

        if self.is_fullscreen_without_decoration:
            HyprWindow.fullscreen_toggle(keep_decoration_when_fullscreen=False)
            return

        self.fullscreen_off()

    @staticmethod
    def fullscreen_toggle(keep_decoration_when_fullscreen: bool = True) -> None:
        mode = 1 if keep_decoration_when_fullscreen else 0
        talk.HyprTalk(f"fullscreen {mode}").execute_as_dispatch()

    def float_on(self) -> None:
        if not self._floating:
            talk.HyprTalk("togglefloating").execute_as_dispatch()

    def float_off(self) -> None:
        if self._floating:
            talk.HyprTalk("togglefloating").execute_as_dispatch()

    def selection_prompt(self) -> str:
        greyer = prettyprint.Prettyprint().color_foreground("grey-bright")

        str_class = f"{self._class.split(".")[-1] if self._class else "class?"}"
        if str_class == "firefox-developer-edition":
            str_class = "firefoxd"
        str_class = (
            f"{prettyprint.Prettyprint().cyan(str_class)}" f"{greyer.apply(">")}"
        )

        str_title = self._title or "title?"

        str_addr = (
            f"{greyer.apply(f"// {self._address[:2]}")}"
            f"{greyer.decorate_underline().apply(self._address[2:])}"
        )

        return f"{str_class} {str_title}  {str_addr}"

    def make_master(self) -> None:
        while not self.is_master():
            self.swap_within_workspace(positive_dir=False)

    def is_master(self, restore_focus: bool = True) -> bool:
        is_master = self.address == HyprWorkspace.window_master().address
        if not is_master and restore_focus:
            self.focus()
        return is_master

    def swap_within_workspace(self, positive_dir: bool = True) -> None:
        cmd = "swapnext" if positive_dir else "swapprev"
        talk.HyprTalk(cmd).execute_as_layoutmsg()
