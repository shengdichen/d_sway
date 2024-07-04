import collections.abc as cabc
import os
import tempfile
import typing


class Fzf:
    def __init__(
        self,
        fzf_reverse: bool = True,
        fzf_height_perc: int = 100,
        fzf_no_sort: bool = False,
        fzf_tiebreak: str = "",
    ):
        self._fzf = "fzf"

        self._config_fzf = ""
        if fzf_reverse:
            self._config_fzf = f"{self._config_fzf} --reverse"
        if fzf_height_perc:
            self._config_fzf = f"{self._config_fzf} --height={fzf_height_perc}%"
        if fzf_no_sort:
            self._config_fzf = f"{self._config_fzf} --no-sort"
        if fzf_tiebreak:
            self._config_fzf = f"{self._config_fzf} --tiebreak={fzf_tiebreak}"

    def _exec(
        self,
        choices: typing.Sequence[str],
        config_fzf_extra: typing.Optional[str] = None,
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
        choices = self._exec(choices)
        if not choices:
            raise RuntimeError("fzf/single> nothing chosen")
        return choices[0]

    def choose_multi(self, choices: typing.Sequence[str]) -> cabc.Sequence[str]:
        return self._exec(choices, config_fzf_extra="--multi")
