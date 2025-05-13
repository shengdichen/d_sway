import collections.abc as cabc
import typing

from hyprland import talk


class Launch:
    def __init__(self, cmd: str):
        self._cmd = cmd

    def launch(self, rules: typing.Optional[cabc.Sequence[str]] = None) -> None:
        cmd = "exec"
        if rules:
            cmd = f"{cmd} [{','.join(rules)}]"
        cmd = f"{cmd} {self._cmd}"
        talk.HyprTalk(cmd).execute_as_dispatch()

    @staticmethod
    def launch_foot(
        cmd_extra: str = "", use_footclient: bool = False, as_float: bool = True
    ) -> None:
        cmd = "footclient" if use_footclient else "foot"
        if cmd_extra:
            cmd = f"{cmd} {cmd_extra}"

        if as_float:
            Launch(cmd).launch(["float"])
        else:
            Launch(cmd).launch()
