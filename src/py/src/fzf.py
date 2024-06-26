import collections.abc as cabc
import os
import tempfile
import typing


class Fzf:
    def __init__(self, fzf_reverse: bool = True, fzf_height_perc: int = 37):
        self._fzf = "fzf"

        self._config_fzf = f"--height={fzf_height_perc}%"
        if fzf_reverse:
            self._config_fzf = f"{self._config_fzf} --reverse"

    def _exec(
        self, choices: typing.Sequence[str], config_fzf_extra: str
    ) -> cabc.Sequence[str]:
        config_fzf = (
            f"{self._config_fzf} {config_fzf_extra}"
            if config_fzf_extra
            else self._config_fzf
        )
        with tempfile.NamedTemporaryFile() as choices_f:
            choices_f.write("\n".join(choices).encode("utf-8"))
            choices_f.flush()

            with tempfile.NamedTemporaryFile() as selection_f:
                os.system(
                    f'{self._fzf} {config_fzf} <"{choices_f.name}" >"{selection_f.name}"'
                )

                with open(selection_f.name, encoding="utf-8") as f:
                    return [line.rstrip() for line in f]

    def choose_one(self, choices: typing.Sequence[str]) -> str:
        return self._exec(choices, self._config_fzf)[0]

    def choose_multi(self, choices: typing.Sequence[str]) -> cabc.Sequence[str]:
        return self._exec(choices, config_fzf_extra="--multi")
