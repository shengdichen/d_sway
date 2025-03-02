import collections.abc as cabc
import logging
import re
import typing

from common import prettyprint
from sway import command
from sway.talk import talk

logger = logging.getLogger(__name__)


class Container:
    def __init__(self):
        self._children: list[Container] = []  # type: ignore [annotation-unchecked]

    @property
    def children(self) -> list["Container"]:
        return self._children

    def is_window(self) -> bool:
        return not bool(self._children)

    def iterate_to_window(self) -> cabc.Generator["Container", None, None]:
        if self.is_window():
            yield self
        for child in self._children:
            yield from child.iterate_to_window()

    def iterate(self) -> cabc.Generator["Container", None, None]:
        yield self
        for child in self._children:
            yield from child.iterate()


class Window(Container):
    PATTERN_SELECTION_PROMPT = re.compile(r"^.* (\d*)$")

    def __init__(
        self,
        _class: str,
        title: str,
        is_xwayland: bool = False,
        #
        is_current: bool = False,
        #
        identifier: int = -1,
    ):
        super().__init__()

        self._class, self._title = _class, title
        self._is_xwayland = is_xwayland

        self._is_current = is_current

        self._identifier = identifier

    def __str__(self) -> str:
        return f"window-{self._identifier}> '{self._class}'/'{self._title}'"

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, int):
            return self._identifier == that
        if isinstance(that, Window):
            return self._identifier == that._identifier
        return False

    @property
    def is_current(self) -> bool:
        return self._is_current

    @classmethod
    def from_json(cls, j: dict) -> "Window":
        if j["app_id"]:
            return cls(
                _class=j["app_id"],
                title=j["name"],
                is_xwayland=False,
                #
                is_current=j["focused"],
                #
                identifier=j["id"],
            )

        return cls(
            _class=j["window_properties"]["class"],
            title=j["window_properties"]["title"],
            is_xwayland=True,
            #
            is_current=j["focused"],
            #
            identifier=j["id"],
        )

    @staticmethod
    def json_is_valid(j: dict) -> bool:
        # alternative implementation:
        #   j["type"] == "con" and j["type"] == "none"
        return "app_id" in j

    def format(self) -> str:
        greyer = prettyprint.Prettyprint().color_foreground("grey-bright")

        _class = f"{self._class.split('.')[-1] if self._class else 'class?'}"
        if _class == "firefox-developer-edition":
            _class = "firefoxd"
        str_class = prettyprint.Prettyprint().cyan(_class)
        if self._is_xwayland:
            str_class += greyer.apply("/X")
        str_class += greyer.apply(">")

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
        return command.Command.cmd_window_goto(self._identifier)

    def swap(self) -> None:
        talk.execute(self.cmd_swap())

    def cmd_swap(self) -> str:
        return f"swap container with con_id {self._identifier}"


class WindowError(ValueError):
    pass


class Group(Container):
    def __init__(
        self,
        layout: str,
        #
        identifier: int | str = -1,
    ):
        super().__init__()

        self._layout = layout

        self._windows: list[Window] = []
        self._subgroups: list[Group] = []

        self._identifier = identifier

    def __str__(self) -> str:
        return (
            f"group-{self._identifier}> '{self._layout}', "
            f"#children={len(self._children)} "
            f"(#windows={len(self._windows)} + #subgroups={len(self._subgroups)})"
        )

    @property
    def windows(self) -> list[Window]:
        return self._windows

    @property
    def subgroups(self) -> list["Group"]:
        return self._subgroups

    @classmethod
    def from_json(cls, j: dict) -> "Group":
        return cls(layout=j["layout"], identifier=j["id"])

    @staticmethod
    def json_is_valid(j: dict) -> bool:
        return j["type"] == "con" and j["layout"] != "none"

    def build_to_window(self, j: dict) -> None:
        for _j in j["nodes"]:
            if Window.json_is_valid(_j):
                window = Window.from_json(_j)
                logger.debug(f"tree/build> [{self}] += [{window}]")
                self.children.append(window)
                self.windows.append(window)
                continue

            group = Group.from_json(_j)
            logger.debug(f"tree/build> [{self}] += [{group}]")
            self.children.append(group)
            self.subgroups.append(group)
            group.build_to_window(_j)

    def format_as_toplevel(self) -> str:
        return f"(toplevel){self}"

    def iterate_to_window(self) -> cabc.Generator[Window, None, None]:
        for child in self._children:
            if child.is_window():
                yield child  # type: ignore
                continue
            yield from child.iterate_to_window()  # type: ignore

    def iterate(self) -> cabc.Generator[Container, None, None]:
        yield self
        for child in self._children:
            yield from child.iterate()


class GroupError(ValueError):
    pass


class Workspace:
    def __init__(
        self,
        name: str,
        #
        identifier: int = -1,
    ):
        self._name = name

        self._toplevel: Group
        self._windows: list[Window] = []

        self._identifier = identifier

    def __str__(self) -> str:
        if self._toplevel:
            str_toplevel = f"[{self._toplevel.format_as_toplevel()}]"
        else:
            str_toplevel = "top-level group tbd"
        return (
            f"workspace-{self._identifier}> '{self._name}', "
            f"#windows {len(self._windows)}, "
            f"{str_toplevel}"
        )

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, str):
            return self._name == that
        if isinstance(that, Workspace):
            return self._name == that._name
        return False

    @property
    def toplevel(self) -> Group:
        return self._toplevel

    @toplevel.setter
    def toplevel(self, value: Group) -> None:
        self._toplevel = value

    @property
    def windows(self) -> list[Window]:
        return self._windows

    @classmethod
    def from_json(cls, j: dict) -> "Workspace":
        workspace = cls(name=j["name"], identifier=j["id"])

        # sway does not make a separate, toplevel group (layout) for workspaces; let's
        # construct it outselves
        group = Group(
            layout=j["layout"],
            identifier=f"w{j['id']}",  # a pseudo-identifier to indiciate the parent-workspace
        )
        workspace.toplevel = group

        return workspace

    @staticmethod
    def json_is_valid(j: dict) -> bool:
        return j["type"] == "workspace"

    def build_to_window(self, j: dict) -> None:
        logger.debug(f"tree/build> [{self}] += [{self._toplevel}]")
        self._toplevel.build_to_window(j)
        self.finalize()

    def finalize(self) -> None:
        for window in self._toplevel.iterate_to_window():
            self._windows.append(window)

    def goto(self) -> None:
        talk.execute(self.cmd_goto())

    def cmd_goto(self) -> str:
        return command.Command.cmd_workspace_goto(self._name)

    def add_current(self) -> str:
        return talk.execute(self.cmd_add_current())

    def cmd_add_current(self) -> str:
        return f"move container workspace {self._name}"


class WorkspaceError(ValueError):
    pass


class Monitor:
    def __init__(
        self,
        name: str,
        #
        identifier: int = -1,
    ):
        self._name = name

        self._workspaces: list[Workspace] = []

        self._identifier = identifier

    def __str__(self) -> str:
        return f"monitor> '{self._name}', #workspaces: {len(self._workspaces)}"

    def __eq__(self, that: typing.Any) -> bool:
        if isinstance(that, str):
            return self._name == that
        if isinstance(that, Monitor):
            return self._name == that._name
        return False

    @property
    def workspaces(self) -> list[Workspace]:
        return self._workspaces

    @classmethod
    def from_json(cls, j: dict) -> "Monitor":
        return cls(name=j["name"], identifier=j["id"])

    @staticmethod
    def json_is_valid(j: dict) -> bool:
        return j["type"] == "output"

    def add_current(self) -> str:
        return talk.execute(self.cmd_add_current())

    def cmd_add_current(self) -> str:
        return f"move workspace output {self._name}"


class MonitorError(ValueError):
    pass


class Root:
    def __init__(
        self,
        name: str,
        #
        identifier: int,
    ):
        self._name = name

        self._monitors: list[Monitor] = []

        self._identifier = identifier

    def __str__(self) -> str:
        return f"root> '{self._name}' (id = {self._identifier})"

    @property
    def monitors(self) -> list[Monitor]:
        return self._monitors

    @classmethod
    def from_json(cls, j: dict) -> "Root":
        return cls(
            name=j["name"],
            #
            identifier=j["id"],
        )

    @staticmethod
    def json_is_valid(j: dict) -> bool:
        return j["type"] == "root"
