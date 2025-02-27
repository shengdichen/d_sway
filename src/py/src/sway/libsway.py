import collections.abc as cabc
import logging
import re
import time
import typing

from common import fzf, prettyprint
from sway import talk as talksway

logger = logging.getLogger(__name__)
talk = talksway.TalkSway()


class Execute:
    @staticmethod
    def cmd_window_goto(window: int) -> str:
        return f"[con_id={window}] focus"

    @staticmethod
    def cmd_workspace_goto(workspace: str) -> str:
        return f"workspace {workspace}"

    @staticmethod
    def cmd_workspace_goto_prev() -> str:
        return "workspace back_and_forth"

    @staticmethod
    def cmd_window_move_workspace_prev() -> str:
        return "move container workspace back_and_forth"

    @staticmethod
    def cmd_opacity_toggle(val: float) -> str:
        # REF:
        #   https://github.com/swaywm/sway/issues/7173#issuecomment-1551364058

        MAX = 1.0

        # find increment that would trigger an overshoot
        incr = 0.05
        while incr + val <= MAX:
            incr *= 2

        logger.debug(f"window/opacity-toggle> probing with increment [{incr}]")
        ret = talk.execute("opacity plus 0.01")
        if "error" in ret[0]:  # overshot
            logger.info(f"window/opacity-toggle> {val}")
            return f"opacity set {val}"

        logger.info(f"window/opacity-toggle> resetting (to {MAX})")
        return f"opacity set {MAX}"

    @staticmethod
    def assemble(cmds: cabc.Iterable[str]) -> str:
        return "; ".join(
            [c for c in cmds if c]  # keep only non-empty commands
        )


class Util:
    @staticmethod
    def traverse(node: dict) -> cabc.Generator[dict, None, None]:
        if "app_id" in node:
            yield node
        for n in node["nodes"]:
            yield from Util.traverse(n)


class Window:
    PATTERN_SELECTION_PROMPT = re.compile(r"^.* (\d*)$")

    def __init__(
        self,
        identifier: int,
        #
        _class: str,
        title: str,
    ):
        self._identifier = identifier
        self._class, self._title = _class, title

    def __str__(self) -> str:
        return f"window> '{self._class}'.'{self._title}' // {self._identifier}"

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, int):
            return self._identifier == that
        if isinstance(that, Window):
            return self._identifier == that._identifier
        return False

    @property
    def identifier(self) -> int:
        return self._identifier

    @classmethod
    def from_json(cls, j: dict) -> "Window":
        if j["app_id"]:
            _class = j["app_id"]
            title = j["name"]
        else:  # xwayland
            _class = j["window_properties"]["class"]
            title = j["window_properties"]["title"]
        return cls(j["id"], _class=_class, title=title)

    @staticmethod
    def traverse(j: dict) -> cabc.Generator[dict, None, None]:
        if "app_id" in j:
            yield j
        for _j in j["nodes"]:
            yield from Window.traverse(_j)

    @classmethod
    def from_node(cls, j: dict) -> cabc.Generator["Window", None, None]:
        if "app_id" in j:
            yield cls.from_json(j)
        for _j in j["nodes"]:
            yield from cls.from_node(_j)

    def format(self) -> str:
        greyer = prettyprint.Prettyprint().color_foreground("grey-bright")

        str_class = f"{self._class.split('.')[-1] if self._class else 'class?'}"
        if str_class == "firefox-developer-edition":
            str_class = "firefoxd"
        str_class = f"{prettyprint.Prettyprint().cyan(str_class)}{greyer.apply('>')}"

        str_title = self._title or "title?"

        str_addr = f"{greyer.apply(f'// {self._identifier}')}"

        return f"{str_class} {str_title}  {str_addr}"

    @staticmethod
    def deformat(s: str) -> int:
        m = Window.PATTERN_SELECTION_PROMPT.match(s)
        if not m:
            raise RuntimeError(f"window> invalid choice {s}")
        return int(m.group(1))

    @staticmethod
    def footclient(cmd: str = "") -> None:
        talk.execute(f"exec footclient {cmd}")

    def goto(self) -> None:
        talk.execute(self.cmd_goto())

    def cmd_goto(self) -> str:
        return Execute.cmd_window_goto(self._identifier)

    def swap(self) -> None:
        talk.execute(self.cmd_swap())

    def cmd_swap(self) -> str:
        return f"swap container with con_id {self._identifier}"


class WindowError(ValueError):
    pass


class Workspace:
    def __init__(self, name: str):
        self._name = name
        self._windows: list[Window] = []

    def __str__(self) -> str:
        return f"workspace> '{self._name}', #windows: {len(self._windows)}"

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, str):
            return self._name == that
        if isinstance(that, Workspace):
            return self._name == that._name
        return False

    @classmethod
    def from_json(cls, j: dict) -> "Workspace":
        return cls(j["name"])

    def windows(self) -> list[Window]:
        return self._windows

    def has(self, window: typing.Any) -> bool:
        return window in self._windows

    def goto(self) -> None:
        talk.execute(self.cmd_goto())

    def cmd_goto(self) -> str:
        return Execute.cmd_workspace_goto(self._name)

    def add_current(self) -> str:
        return talk.execute(self.cmd_add_current())

    def cmd_add_current(self) -> str:
        return f"move container workspace {self._name}"


class WorkspaceError(ValueError):
    pass


class Monitor:
    def __init__(self, name: str) -> None:
        self._name = name
        self._workspaces: list[Workspace] = []

    def __str__(self) -> str:
        return f"monitor> '{self._name}', #workspaces: {len(self._workspaces)}"

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, str):
            return self._name == that
        if isinstance(that, Monitor):
            return self._name == that._name
        return False

    @classmethod
    def from_json(cls, j: dict) -> "Monitor":
        return cls(j["name"])

    def workspaces(self) -> list[Workspace]:
        return self._workspaces

    def has(self, workspace: typing.Any) -> bool:
        return workspace in self._workspaces

    def add_current(self) -> str:
        return talk.execute(self.cmd_add_current())

    def cmd_add_current(self) -> str:
        return f"move workspace output {self._name}"


class MonitorError(ValueError):
    pass


class HoldSway(Workspace):
    NAME = "HOLD"

    def __init__(self):
        super().__init__(name=HoldSway.NAME)

    def split(self, window: Window) -> str:
        logger.info(f"hold> split [{window}]")
        cmds = [
            window.cmd_goto(),
            Execute.cmd_window_move_workspace_prev(),
            window.cmd_goto(),
        ]
        return Execute.assemble(cmds)


class Management:
    def __init__(self):
        self._monitors = []
        self._workspaces = []
        self._hold = HoldSway()

        self._current: tuple[Monitor, Workspace, typing.Optional[Window]] = ()

        self._fzf = fzf.Fzf(fzf_tiebreak="index")

    def load(self) -> None:
        for j in talk.nodes()["nodes"]:
            monitor = Monitor.from_json(j)
            logger.debug(f"management/load> [{monitor}]")
            self._monitors.append(monitor)

            for j in j["nodes"]:
                workspace = Workspace.from_json(j)
                logger.debug(f"management/load> [{workspace}]")
                monitor.workspaces().append(workspace)

                if workspace != self._hold:
                    self._workspaces.append(workspace)

                for j in Window.traverse(j):
                    window = Window.from_json(j)
                    logger.debug(f"management/load> [{window}]")

                    if j["focused"]:
                        self._current = (monitor, workspace, window)

                    if workspace != self._hold:
                        workspace.windows().append(window)
                        continue
                    self._hold.windows().append(window)

    def current(self) -> tuple[Monitor, Workspace, typing.Optional[Window]]:
        if not self._current:
            logger.info(
                "management/current> no window focused, querying monitor & workspace..."
            )
            for j in talk.workspaces():
                if j["focused"]:
                    self._current = (
                        self.monitor_find(j["output"]),
                        self.workspace_find(j["name"]),
                        None,
                    )
                    break
            else:
                logger.error(
                    "sway> not only no window focused, but no workspace either"
                )
                raise RuntimeError  # this should never happen

        logger.debug(
            "management/current> "
            f"[{self._current[0]}], [{self._current[1]}], [{self._current[2]}]"
        )
        return self._current

    def report(self) -> None:
        print(
            "management/current> "
            f"[{self._current[0]}], [{self._current[1]}], [{self._current[2]}]"
        )
        print()

        print("management/report> windows, nonhold")
        for workspace in self._workspaces:
            for window in workspace.windows():
                print(window)
        print()

        print("management/report> windows, hold")
        for window in self._hold.windows():
            print(window)

    def monitor_find(self, query: typing.Any) -> Monitor:
        for monitor in self._monitors:
            if monitor == query:
                return monitor
        raise MonitorError

    def monitor_of(self, workspace: Workspace) -> Monitor:
        for monitor in self._monitors:
            if monitor.has(workspace):
                return monitor
        raise MonitorError

    def workspace_find(self, query: typing.Any) -> Workspace:
        for workspace in self._workspaces:
            if workspace == query:
                return workspace
        raise WorkspaceError

    def window_find(self, query: typing.Any) -> Window:
        for workspace in self._workspaces:
            for window in workspace.windows():
                if window == query:
                    return window
        for window in self._hold.windows():
            if window == query:
                return window
        raise WindowError

    def hold_add_current(self) -> None:
        cmds = []

        cmds.append(
            self._hold.windows()[-1].cmd_goto()  # make sure new window is added last
        )
        monitor = self.current()[0]
        if self.monitor_of(self._hold) != monitor:
            cmds.append(monitor.cmd_add_current())  # already on hold-workspace
        cmds.append(Execute.cmd_workspace_goto_prev())

        cmds.append(self._hold.cmd_add_current())

        talk.execute(Execute.assemble(cmds))

    def hold_unique(self) -> None:
        cmds = []

        if not (window := self.current()[2]):
            logger.warning("sway/hold-unique> no current window, skipping")
            return

        workspace = self.current()[1]
        windows = workspace.windows()
        if len(windows) == 1:
            logger.warning(
                f"sway/hold-unique> only [{window}] on [{workspace}], skipping"
            )
            return

        # make sure new window is added last
        cmds.append(self._hold.windows()[-1].cmd_goto())
        monitor = self.current()[0]
        if self.monitor_of(self._hold) != monitor:
            cmds.append(monitor.cmd_add_current())
        cmds.append(Execute.cmd_workspace_goto_prev())

        logger.info(f"sway/hold-unique> keeping [{window}]")
        for w in windows:
            if w == window:
                continue
            logger.info(f"sway/hold-unique> discarding [{w}]")
            cmds.append(w.cmd_goto())
            cmds.append(self._hold.cmd_add_current())

        talk.execute(Execute.assemble(cmds))

    def hold_split(self) -> None:
        cmds = []

        monitor = self.current()[0]
        if self.monitor_of(self._hold) != monitor:
            cmds.append(self._hold.cmd_goto())
            cmds.append(monitor.cmd_add_current())

        windows = list(reversed(self._hold.windows()))  # newest first
        for s in self._fzf.choose_multi((w.format() for w in windows)):
            window = windows[windows.index(Window.deformat(s))]
            cmds.append(self._hold.split(window))

        talk.execute(Execute.assemble(cmds))

    def hold_swap(self, window_id: typing.Optional[int] = None) -> None:
        cmds = []

        monitor = self.current()[0]
        if self.monitor_of(self._hold) != monitor:
            cmds.append(self._hold.cmd_goto())
            cmds.append(monitor.cmd_add_current())  # already on hold-workspace
            cmds.append(Execute.cmd_workspace_goto_prev())

        if window_id:
            window = self.window_find(window_id)
            cmds.append(window.cmd_goto())

        windows = list(reversed(self._hold.windows()))  # newest first
        i = windows.index(
            Window.deformat(self._fzf.choose_one((w.format() for w in windows)))
        )
        window_new = windows[i]
        cmds.append(window_new.cmd_swap())

        # make swapped window last in hold
        cmds.append(self._hold.cmd_goto())
        for __ in range(i):
            cmds.append("move right")
        cmds.append(Execute.cmd_workspace_goto_prev())

        logger.info(
            f"swap> [{window if window_id else 'current'}] <-> "
            f"{i}/{len(self._hold.windows())}.[{window_new}]"
        )
        talk.execute(Execute.assemble(cmds))

    def footclient(self, cmd: str = "") -> Window:
        return self.launch_float(f"footclient {cmd}")

    def launch_float(
        self, cmd: str, n_checks: int = 30, check_cadence: float = 0.03
    ) -> Window:
        window = self.current()[2]
        talk.execute(f"exec {cmd}")

        if window:
            for __ in range(n_checks):
                if (window_new := self._window_current()) == window:
                    time.sleep(check_cadence)
                    continue
                logger.info(
                    f"sway/launch> '{cmd}': [{window_new}] "
                    f"(previously [{window if window else 'empty'}])"
                )
                talk.execute("floating enable")
                return window_new
            raise WindowError

        # no currently focused window
        for __ in range(n_checks):
            for j in Util.traverse(talk.nodes()):
                if not j["focused"]:
                    continue
                window_new = Window.from_json(j)
                logger.info(f"sway/launch> '{cmd}': [{window_new}]")
                talk.execute("floating enable")
                return window_new
            time.sleep(check_cadence)
        raise WindowError

    def _window_current(self) -> Window:
        for j in Util.traverse(talk.nodes()):
            if j["focused"]:
                return Window.from_json(j)
        raise WindowError

    def opacity_toggle(self, val: float = 0.90625) -> None:
        if not self.current()[2]:
            logger.warning("sway/opacity-toggle> no current window, skipping")
            return

        talk.execute(Execute.cmd_opacity_toggle(val))
