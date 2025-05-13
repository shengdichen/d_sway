import collections.abc as cabc
import logging
import time
import typing

from common import fzf
from sway import command
from sway import node as nodesway
from sway.talk import talk

logger = logging.getLogger(__name__)


class Util:
    @staticmethod
    def traverse(node: dict) -> cabc.Generator[dict, None, None]:
        if Util.is_leaf(node):
            yield node
        for n in node["nodes"]:
            yield from Util.traverse(n)

    @staticmethod
    def traverse_to_container(node: dict) -> cabc.Generator[dict, None, None]:
        if node["nodes"] and Util.is_leaf(node["nodes"][0]):
            yield node
        for n in node["nodes"]:
            yield from Util.traverse_to_container(n)

    @staticmethod
    def is_leaf(node: dict) -> bool:
        return "app_id" in node


class HoldSway(nodesway.Workspace):
    NAME = "HOLD"

    def __init__(
        self,
        #
        identifier: int = -1,
    ):
        super().__init__(name=HoldSway.NAME, identifier=identifier)

    def split(self, window: nodesway.Window) -> str:
        logger.info(f"hold> split [{window}]")

        cmd = command.Command()
        cmd.add(window.cmd_goto())
        cmd.add(command.Command.cmd_window_move_workspace_prev())
        cmd.add(window.cmd_goto())
        return cmd.assemble()

    @classmethod
    def from_json(cls, j: dict) -> "HoldSway":
        workspace: HoldSway = cls(identifier=j["id"])

        group = nodesway.Group(
            layout=j["layout"],
            identifier=f"w{j['id']}",
        )
        workspace.toplevel = group  # pylint: disable=attribute-defined-outside-init

        return workspace


class Management:
    def __init__(self):
        self._raw = talk.nodes()
        self._root = nodesway.Root.from_json(self._raw)

        self._hold: HoldSway  # type: ignore [annotation-unchecked]

        self._current_monitor: nodesway.Monitor  # type: ignore [annotation-unchecked]
        self._current_workspace: nodesway.Workspace  # type: ignore [annotation-unchecked]
        self._current_window: typing.Optional[nodesway.Window]  # type: ignore

        self._fzf = fzf.Fzf(fzf_tiebreak="index")

    @property
    def current_window(self) -> typing.Optional[nodesway.WindowError]:
        return self._current_window

    def load_tree(self) -> None:
        for j in self._raw["nodes"]:
            monitor = nodesway.Monitor.from_json(j)
            logger.debug(f"tree/build> [{self._root}] += [{monitor}]")
            self._root.monitors.append(monitor)

            logger.debug(f"tree/build> start: [{monitor}]")

            for j in j["nodes"]:
                if j["name"] == HoldSway.NAME:
                    workspace = HoldSway.from_json(j)
                    self._hold = workspace
                else:
                    workspace = nodesway.Workspace.from_json(j)

                logger.debug(f"tree/build> [{monitor}] += [{workspace}]")
                monitor.workspaces.append(workspace)

                logger.debug(f"tree/build> start: [{workspace}]")
                workspace.build_to_window(j)
                logger.debug(f"tree/build> end: [{workspace}]")

            logger.debug(f"tree/build> end: [{monitor}]")

    def load_current(self) -> None:
        for monitor in self._root.monitors:
            for workspace in monitor.workspaces:
                for window in workspace.toplevel.iterate_to_window():
                    if not window.is_current:
                        continue
                    (
                        self._current_monitor,
                        self._current_workspace,
                        self._current_window,
                    ) = monitor, workspace, window
                    logger.info(
                        "management/current> "
                        f"[{self._current_monitor}]->"
                        f"[{self._current_workspace}]->"
                        f"[{self._current_window}]"
                    )
                    return

        for j in talk.workspaces():
            if not j["focused"]:
                continue
            self._current_monitor = self.monitor_find(j["output"])
            self._current_workspace = self.workspace_find(j["name"])
            logger.info(
                "management/current> "
                f"[{self._current_monitor}]->"
                f"[{self._current_workspace}], "
                "no current window"
            )
            return

        logger.error("sway> not only no window focused, but no workspace either")
        raise RuntimeError  # this should never happen

    def load(self) -> None:
        self.load_tree()
        self.load_current()

    def report(self) -> None:
        print(
            "management/current> "
            f"[{self._current_monitor}]->"
            f"[{self._current_workspace}]->"
            f"[{self._current_window}]"
        )
        print()
        print()

        self.report_tree()
        print()

        print("management/report> windows, hold")
        for window in self._hold.windows:
            print(window)

    def report_tree(self) -> None:
        for monitor in self._root.monitors:
            print(monitor)
            for workspace in monitor.workspaces:
                print(workspace)
                for node in workspace.toplevel.iterate():
                    print(node)
                print()

    def monitor_find(self, query: typing.Any) -> nodesway.Monitor:
        for monitor in self._root.monitors:
            if monitor == query:
                return monitor
        raise nodesway.MonitorError

    def monitor_of(self, workspace: nodesway.Workspace) -> nodesway.Monitor:
        for monitor in self._root.monitors:
            if workspace in monitor.workspaces:
                logger.info(f"found monitor [{monitor}]")
                return monitor
        raise nodesway.MonitorError

    def workspace_find(self, query: typing.Any) -> nodesway.Workspace:
        for monitor in self._root.monitors:
            for workspace in monitor.workspaces:
                if workspace == query:
                    return workspace
        raise nodesway.WorkspaceError

    def window_find(self, query: typing.Any) -> nodesway.Window:
        for monitor in self._root.monitors:
            for workspace in monitor.workspaces:
                for window in workspace.windows:
                    if window == query:
                        return window
        for window in self._hold.windows:
            if window == query:
                return window
        raise nodesway.WindowError

    def hold_add_current(self) -> None:
        cmd = command.Command()

        cmd.add(self._hold_to_current_monitor())
        cmd.add(self._hold.cmd_add_current())

        cmd.execute()

    def hold_unique_container(self) -> None:
        # unique in container
        self._hold_unique(mode=0)

    def hold_unique_container_workspace(self) -> None:
        # first unique in container, then unique in workspace
        self._hold_unique(mode=1)

    def hold_unique_workspace(self) -> None:
        # unique in workspace
        self._hold_unique(mode=2)

    def _hold_unique(self, mode: int = 0) -> None:
        cmd = command.Command()

        if not (window := self._current_window):
            logger.warning("sway/hold-unique> no current window, skipping")
            return

        workspace = self._current_workspace
        windows = workspace.windows
        if len(windows) == 1:
            logger.warning(
                f"sway/hold-unique> only [{window}] on [{workspace}], skipping"
            )
            return

        cmd.add(self._hold_to_current_monitor())

        if mode <= 1:
            for container in Util.traverse_to_container(talk.nodes()):
                windows_c = [nodesway.Window.from_json(j) for j in container["nodes"]]
                if window not in windows_c:
                    continue

                n_windows = len(windows_c)
                if n_windows == 1:
                    if mode == 0:
                        logger.warning(
                            f"sway/hold-unique> only [{window}] in container "
                            f"[{container['id']}/{container['layout']}], skipping"
                        )
                        return
                    logger.info(
                        f"sway/hold-unique> current [{window}] alone in container "
                        f"[{container['id']}/{container['layout']}]; "
                        f"working on [{workspace}] now"
                    )
                    break

                logger.info(
                    f"sway/hold-unique> working on container "
                    f"[{container['id']}/{container['layout']}] with {n_windows} windows]"
                )
                windows = windows_c
                break

        for w in windows:
            if w == window:
                continue
            logger.debug(f"sway/hold-unique> discarding [{w}]")
            cmd.add(w.cmd_goto())
            cmd.add(self._hold.cmd_add_current())

        cmd.execute()

    def _hold_to_current_monitor(self, visit_last_window: bool = True) -> str:
        cmd = command.Command()

        if visit_last_window:
            # make sure new window is added last
            cmd.add(self._hold.windows[-1].cmd_goto())

        if self.monitor_of(self._hold) != self._current_monitor:
            cmd.add(self._current_monitor.cmd_add_current())
        cmd.add(command.Command.cmd_workspace_goto_prev())

        return cmd.assemble()

    def hold_split(self) -> None:
        cmd = command.Command()

        if self.monitor_of(self._hold) != self._current_monitor:
            cmd.add(self._hold.cmd_goto())
            cmd.add(self._current_monitor.cmd_add_current())

        windows = list(reversed(self._hold.windows))  # newest first
        for s in self._fzf.choose_multi((w.format() for w in windows)):
            window = windows[windows.index(nodesway.Window.deformat(s))]
            logger.info(f"miao {self._hold.split(window)}")
            cmd.add(self._hold.split(window))

        cmd.execute()

    def hold_swap(self, window_id: typing.Optional[int] = None) -> None:
        cmd = command.Command()

        monitor = self._current_monitor
        if self.monitor_of(self._hold) != monitor:
            cmd.add(self._hold.cmd_goto())
            cmd.add(monitor.cmd_add_current())  # already on hold-workspace
            cmd.add(command.Command.cmd_workspace_goto_prev())

        if window_id:
            window = self.window_find(window_id)
            cmd.add(window.cmd_goto())

        windows = list(reversed(self._hold.windows))  # newest first
        i = windows.index(
            nodesway.Window.deformat(
                self._fzf.choose_one((w.format() for w in windows))
            )
        )
        window_new = windows[i]
        cmd.add(window_new.cmd_swap())

        # make swapped window last in hold
        cmd.add(self._hold.cmd_goto())
        for __ in range(i):
            cmd.add("move right")
        cmd.add(command.Command.cmd_workspace_goto_prev())

        logger.info(
            f"swap> [{window if window_id else 'current'}] <-> "
            f"{i}/{len(self._hold.windows)}.[{window_new}]"
        )
        cmd.execute()

    def footclient(self, cmd: str = "") -> nodesway.Window:
        return self.launch_float(f"footclient {cmd}")

    def launch_float(
        self, cmd: str, n_checks: int = 30, check_cadence: float = 0.03
    ) -> nodesway.Window:
        window = self._current_window
        logger.info(f"old {window}")
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
            raise nodesway.WindowError

        # no currently focused window
        for __ in range(n_checks):
            for j in Util.traverse(talk.nodes()):
                if not j["focused"]:
                    continue
                window_new = nodesway.Window.from_json(j)
                logger.info(f"sway/launch> '{cmd}': [{window_new}]")
                talk.execute("floating enable")
                return window_new
            time.sleep(check_cadence)
        raise nodesway.WindowError

    def _window_current(self) -> nodesway.Window:
        for j in Util.traverse(talk.nodes()):
            if j["focused"]:
                return nodesway.Window.from_json(j)
        raise nodesway.WindowError

    def opacity_toggle(self, val: float = 0.90625) -> None:
        if not self._current_window:
            logger.warning("sway/opacity-toggle> no current window, skipping")
            return

        command.Command().add(command.Command.cmd_opacity_toggle(val)).execute()
