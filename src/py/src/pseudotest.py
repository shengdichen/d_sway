import abstraction


class TestAbstraction:
    def test_monitors(self):
        for monitor in abstraction.HyprMonitor.monitors():
            monitor.print()

    def test_workspace(self) -> None:
        abstraction.HyprWorkspace.from_current().print()
        abstraction.HyprWorkspace.from_hold().print()

        for ws in abstraction.HyprWorkspace.workspaces():
            ws.print()

    def test_window(self) -> None:
        abstraction.HyprWindow.from_current().print()
        abstraction.HyprWindow.from_previous().print()
        abstraction.HyprWindow.from_previous_relative().print()


if __name__ == "__main__":
    TestAbstraction().test_monitors()
    TestAbstraction().test_workspace()
    TestAbstraction().test_window()
