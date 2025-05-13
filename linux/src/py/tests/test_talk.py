import pytest

from src import talk


class TestHyprTalk:
    def test_to_json(self) -> None:
        res = talk.HyprTalk("version").execute_to_json()
        for k in ["branch", "commit", "tag"]:
            assert k in res

    def test_to_string(self) -> None:
        res = talk.HyprTalk("version").execute_to_str()
        assert isinstance(res, str)

    def test_error(self) -> None:
        with pytest.raises(ValueError):
            talk.HyprTalk("_version").execute_to_json()

        with pytest.raises(ValueError):
            talk.HyprTalk("_fullscreen").execute_to_json()
