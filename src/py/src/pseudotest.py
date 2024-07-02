import abstraction
import hold


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


class TestHolding:
    def test_pull_append(self) -> None:
        hold.Holding.pull_append()
        hold.Holding.pull_replace()

    def test_pull_replace(self) -> None:
        hold.Holding.pull_replace()

    def test_hold_previous(self) -> None:
        window = abstraction.HyprWindow.from_previous()
        hold.Holding().push(window)


if __name__ == "__main__":
    TestAbstraction().test_monitors()
    TestAbstraction().test_workspace()
    TestAbstraction().test_window()

    TestHolding().test_hold_previous()
