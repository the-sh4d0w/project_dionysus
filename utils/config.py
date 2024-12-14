"""Config util."""

import pathlib
import typing

import pydantic
import pydantic_core

CONFIG_PATH = "config/config.json"
SOUNDS_PATH = "config/sounds.json"


class Sound(pydantic.BaseModel):
    """Sound representation."""
    text: typing.Optional[str] = None
    emoji: typing.Optional[str] = None  # trying to match emojis isn't worth it


class Sounds(pydantic.RootModel):
    """Sounds representation."""
    root: dict[str, Sound] = {}

    @classmethod
    def load(cls) -> "Sounds":
        """Load the config from file."""
        return Sounds.model_validate(pydantic_core.from_json(
            pathlib.Path(SOUNDS_PATH).read_text(encoding="utf-8")))


class Config(pydantic.BaseModel):
    """Config representation."""
    language: str = pydantic.Field(default="en", pattern="^[a-z]{2}$")
    show_clock: bool = False
    default_emoji: str = "🔊"
    theme: str = "textual-dark"

    @classmethod
    def load(cls) -> "Config":
        """Load the config from file."""
        return Config.model_validate(pydantic_core.from_json(
            pathlib.Path(CONFIG_PATH).read_text(encoding="utf-8")))

    def store(self) -> None:
        """Store the config in a file."""
        pathlib.Path(CONFIG_PATH).write_text(self.model_dump_json(),
                                             encoding="utf-8")


CONFIG = Config.load()
SOUNDS = Sounds.load().root
