import os
import pathlib


class Definition:
    DIR_CONFIG: pathlib.Path
    DIR_STATE: pathlib.Path

    LOG_FILE: pathlib.Path
    LOG_FORMAT: str
    LOG_DATEFORMAT: str
    LOG_CONFIG: dict

    def __init__(self):
        # NOTE:
        #   use setup.sh for mkdir'ing these folders
        self.DIR_CONFIG = pathlib.Path(os.environ["HOME"]) / ".config"
        self.DIR_CONFIG_HYPRLAND = self.DIR_CONFIG / "hypr"
        self.DIR_CONFIG_SWAY = self.DIR_CONFIG / "sway"

        self.DIR_STATE = pathlib.Path(os.environ["HOME"]) / ".local" / "state"
        self.DIR_STATE_HYPRLAND = self.DIR_STATE / "hypr"
        self.DIR_STATE_SWAY = self.DIR_STATE / "sway"

        self.LOG_FORMAT = (
            "[%(asctime)s.%(msecs)03d: %(module)s (%(levelname)s)] %(message)s"
        )
        self.LOG_DATEFORMAT = "%Y.%m.%d-%H:%M:%S"

        self.LOG_FILE_HYPRLAND = self.DIR_STATE_HYPRLAND / "log"
        self.LOG_CONFIG_HYPRLAND = {
            "filename": self.LOG_FILE_HYPRLAND,
            "format": self.LOG_FORMAT,
            "datefmt": self.LOG_DATEFORMAT,
        }

        self.LOG_FILE_SWAY = self.DIR_STATE_SWAY / "log"
        self.LOG_CONFIG_SWAY = {
            "filename": self.LOG_FILE_SWAY,
            "format": self.LOG_FORMAT,
            "datefmt": self.LOG_DATEFORMAT,
        }


DEFINITION = Definition()
