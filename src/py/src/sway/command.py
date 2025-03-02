import logging

from sway.talk import talk

logger = logging.getLogger(__name__)


class Command:
    def __init__(self):
        self._cmds = []

    def add(self, cmd: str) -> "Command":
        self._cmds.append(cmd)
        return self

    def assemble(self) -> str:
        return "; ".join(
            [c for c in self._cmds if c]  # keep only non-empty commands
        )

    def execute(self) -> None:
        talk.execute(self.assemble())

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
