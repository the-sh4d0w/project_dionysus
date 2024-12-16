"""Config util."""

import pathlib
import typing

import pydantic
import pydantic_core
import sounddevice

CONFIG_PATH = "config/config.json"
SOUNDS_PATH = "config/sounds.json"

default_in: int
default_out: int
default_in, default_out = typing.cast(
    tuple[int, int], sounddevice.default.device)


def get_input_devices() -> dict[int, tuple[str, int]]:
    """Get all input devices."""
    devices: sounddevice.DeviceList = typing.cast(
        sounddevice.DeviceList, sounddevice.query_devices())
    return {device["index"]: (device["name"], device["max_input_channels"])
            for device in devices if device["max_output_channels"] == 0}


def get_output_devices() -> dict[int, tuple[str, int]]:
    """Get all input devices."""
    devices: sounddevice.DeviceList = typing.cast(
        sounddevice.DeviceList, sounddevice.query_devices())
    return {device["index"]: (device["name"], device["max_output_channels"])
            for device in devices if device["max_input_channels"] == 0}


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
    input_device: int = default_in
    output_device: int = default_out
    virtual_output_device: int = default_out

    @classmethod
    def load(cls) -> "Config":
        """Load the config from file."""
        return Config.model_validate(pydantic_core.from_json(
            pathlib.Path(CONFIG_PATH).read_text(encoding="utf-8")))

    def store(self) -> None:
        """Store the config in a file."""
        pathlib.Path(CONFIG_PATH).write_text(self.model_dump_json(),
                                             encoding="utf-8")

    def store_reset(self) -> None:
        """Store the config in a file and reset audio device selection by excluding them."""
        pathlib.Path(CONFIG_PATH).write_text(self.model_dump_json(
            exclude={"input_device", "output_device", "virtual_output_device"}),
            encoding="utf-8")


CONFIG = Config.load()
SOUNDS = Sounds.load().root
