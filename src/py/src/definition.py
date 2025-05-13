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
        self.DIR_CONFIG = pathlib.Path(os.environ["HOME"]) / ".config" / "hypr"
        self.DIR_STATE = pathlib.Path(os.environ["HOME"]) / ".local" / "state" / "hypr"

        self.LOG_FILE = self.DIR_STATE / "log"
        self.LOG_FORMAT = (
            "[%(asctime)s.%(msecs)03d: %(module)s (%(levelname)s)] %(message)s"
        )
        self.LOG_DATEFORMAT = "%Y.%m.%d-%H:%M:%S"
        self.LOG_CONFIG = {
            "filename": self.LOG_FILE,
            "format": self.LOG_FORMAT,
            "datefmt": self.LOG_DATEFORMAT,
        }


DEFINITION = Definition()
