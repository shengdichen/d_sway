import re


class WindowFormat:
    P_FIREFOX = re.compile(r"(.*) — Firefox Developer Edition$")
    P_FIREFOX_PRIVATE = re.compile(
        r"(.*) — Firefox Developer Edition Private Browsing$"
    )
    P_CHROMIUM = re.compile(r"(.*) - Chromium$")

    def __init__(self, _class: str, title: str):
        self._class, self._title = _class, title

    def format(self) -> tuple[str, str]:
        if self._class == "firefox-developer-edition":
            return self._format_firefoxd()
        if self._class == "Chromium":
            return self._format_chromium()
        if self._class in ("PPSSPPSDL", "PPSSPPQt"):
            return self._format_psp()
        if self._class == "AppRun.wrapped":
            return self._format_ps2()
        if self._class == "rpcs3":
            return self._format_ps3()

        return self._format_default()

    def _format_default(self) -> tuple[str, str]:
        return self._format_default_class(), self._format_default_title()

    def _format_default_class(self) -> str:
        return WindowFormat._keep_final(self._class) if self._class else "class?"

    def _format_default_title(self) -> str:
        return self._title or "title?"

    @staticmethod
    def _keep_final(s: str) -> str:
        return s.split(".")[-1]

    def _format_firefoxd(self) -> tuple[str, str]:
        s_class = "firefoxd"

        if m := WindowFormat.P_FIREFOX.match(self._title):
            return s_class, m.group(1)
        if m := WindowFormat.P_FIREFOX_PRIVATE.match(self._title):
            return s_class, m.group(1)

        return s_class, self._format_default_title()

    def _format_chromium(self) -> tuple[str, str]:
        s_class = self._class.lower()

        if m := WindowFormat.P_CHROMIUM.match(self._title):
            return s_class, m.group(1)

        return s_class, self._format_default_title()

    def _format_psp(self) -> tuple[str, str]:
        _class = "psp" if self._class == "PPSSPPSDL" else "psp-qt"
        return _class, self._format_default_title()

    def _format_ps2(self) -> tuple[str, str]:
        return "ps2", self._format_default_title()

    def _format_ps3(self) -> tuple[str, str]:
        return "ps3", self._format_default_title()
