import collections.abc as cabc
import logging
import re

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
        identifier: int = -1,
    ):
        super().__init__()

        self._class, self._title = _class, title
        self._is_xwayland = is_xwayland

        self._identifier = identifier

    def __str__(self) -> str:
        return f"window-{self._identifier}> '{self._class}'/'{self._title}'"

    @classmethod
    def from_json(cls, j: dict) -> "Window":
        if j["app_id"]:
            return cls(
                _class=j["app_id"],
                title=j["name"],
                is_xwayland=False,
                #
                identifier=j["id"],
            )

        return cls(
            _class=j["window_properties"]["class"],
            title=j["window_properties"]["title"],
            is_xwayland=True,
            #
            identifier=j["id"],
        )

    @staticmethod
    def json_is_valid(j: dict) -> bool:
        # alternative implementation:
        #   j["type"] == "con" and j["type"] == "none"
        return "app_id" in j


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

    def finalize(self) -> None:
        for window in self._toplevel.iterate_to_window():
            self._windows.append(window)


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

    @property
    def workspaces(self) -> list[Workspace]:
        return self._workspaces

    @classmethod
    def from_json(cls, j: dict) -> "Monitor":
        return cls(name=j["name"], identifier=j["id"])

    @staticmethod
    def json_is_valid(j: dict) -> bool:
        return j["type"] == "output"


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
