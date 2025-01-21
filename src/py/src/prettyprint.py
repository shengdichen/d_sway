import typing

# REF:
#   https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences


class Prettyprint:
    COLOR_FOREGROUD = {
        "black": 30,
        "grey-dark": 90,
        "grey-bright": 37,
        "white": 997,
        #
        "red": 31,
        "green": 32,
        "yellow": 33,
        "blue": 34,
        "magenta": 35,
        "cyan": 36,
    }

    COLOR_BACKGROUD = {
        "black": 40,
        "grey-dark": 100,
        "grey-bright": 47,
        "white": 107,
        #
        "red": 41,
        "green": 42,
        "yellow": 43,
        "blue": 44,
        "magenta": 45,
        "cyan": 46,
    }

    DECORATIONS = {
        "bold": 1,
        "faint": 2,
        "italic": 3,
        "underline": 4,
    }

    def __init__(self, atoms: typing.Optional[list[int]] = None):
        self._atoms = atoms or []

    @property
    def atoms(self) -> list[int]:
        return self._atoms

    @classmethod
    def clone(cls, that: "Prettyprint") -> "Prettyprint":
        return cls(list(that.atoms))

    def grey_bright(self, txt: str) -> str:
        return self.color_foreground("grey-bright").apply(txt)

    def grey_dark(self, txt: str) -> str:
        return self.color_foreground("grey-dark").apply(txt)

    def cyan(self, txt: str) -> str:
        return self.color_foreground("cyan").apply(txt)

    def color_foreground(self, color: str) -> "Prettyprint":
        self._atoms.append(Prettyprint.COLOR_FOREGROUD[color])
        return self

    def color_background(self, color: str) -> "Prettyprint":
        self._atoms.append(Prettyprint.COLOR_BACKGROUD[color])
        return self

    def decorate_underline(self) -> "Prettyprint":
        return self.decorate("underline")

    def undecorate_underline(self) -> "Prettyprint":
        self.undecorate("underline")
        return self

    def decorate_bold(self) -> "Prettyprint":
        return self.decorate("bold")

    def undecorate_bold(self) -> "Prettyprint":
        self.undecorate("bold")
        return self

    def decorate(self, decoration: str) -> "Prettyprint":
        atom = Prettyprint.DECORATIONS[decoration]
        if atom not in self._atoms:
            self._atoms.append(atom)
        return self

    def undecorate(self, decoration: str) -> "Prettyprint":
        atom = Prettyprint.DECORATIONS[decoration]
        if atom in self._atoms:
            self._atoms.remove(atom)
        return self

    def apply(self, txt: str) -> str:
        return f"{self._make_segment()}{txt}{self._make_reset()}"

    def _make_segment(self) -> str:
        return f"\033[{";".join((str(a) for a in self._atoms))}m"

    @staticmethod
    def _make_reset() -> str:
        return "\033[0m"
