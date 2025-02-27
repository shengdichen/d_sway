import logging
import pathlib
import sys
import typing

from common.definition import DEFINITION
from sway import libsway

logger = logging.getLogger(__name__)


class Front:
    def hold_add_current(self) -> None:
        m = libsway.Management()
        m.load()
        m.hold_add_current()

    def hold_split_cmd(self) -> None:
        m = libsway.Management()
        m.load()
        m.hold_split()

    def hold_swap_cmd(self, *args) -> None:
        m = libsway.Management()
        m.load()
        m.hold_swap(int(args[0]))

    def test(self) -> None:
        m = libsway.Management()
        m.load()
        m.report()


if __name__ == "__main__":
    logging.basicConfig(**DEFINITION.LOG_CONFIG_SWAY, level=logging.INFO)

    if len(sys.argv) == 1:
        raise RuntimeError("sway> huh? what mode?")

    # pylint: disable=too-many-return-statements,too-many-branches
    def main(mode: typing.Optional[str], *args: str) -> None:
        if mode == "hold-add-current":
            Front().hold_add_current()
            return

        if mode == "hold-unique":
            m = libsway.Management()
            m.load()
            m.hold_unique()
            return

        if mode == "hold-split-cmd":
            Front().hold_split_cmd()
            return
        if mode == "hold-split":
            m = libsway.Management()
            m.load()

            cmd = f"python {pathlib.Path(__file__).resolve()} {mode}-cmd"
            m.footclient(cmd)
            return

        if mode == "hold-swap-cmd":
            Front().hold_swap_cmd(*args)
            return
        if mode == "hold-swap":
            m = libsway.Management()
            m.load()

            if window := m.current()[2]:
                current = window.identifier
                cmd = f"python {pathlib.Path(__file__).resolve()} {mode}-cmd {current}"
                m.footclient(cmd)
                return

            logger.warning(
                "sway/hold-swap> nothing to swap against, splitting from hold instead"
            )
            cmd = f"python {pathlib.Path(__file__).resolve()} hold-split-cmd"
            m.footclient(cmd)
            return

        if mode == "test":
            Front().test()
            return

        logger.error(f"sway> unrecognized mode [{mode}], exiting...")
        raise RuntimeError(f"sway> unrecognized mode [{mode}]")

    main(*sys.argv[1:])
