"""Util stuff."""
import json
import pathlib
import typing

import pydantic
import pydantic.validators
import textual.design

CONFIG_PATH = "config.json"


class Colors(pydantic.BaseModel):
    """Pydantic model to represent the textual ColorSystem."""
    name: str
    dark: bool = False
    primary: str = pydantic.Field(pattern="^#[0-9a-fA-F]{6}$")
    secondary: str = pydantic.Field(default=None, pattern="^#[0-9a-fA-F]{6}$")
    warning: str = pydantic.Field(default=None, pattern="^#[0-9a-fA-F]{6}$")
    error: str = pydantic.Field(default=None, pattern="^#[0-9a-fA-F]{6}$")
    success: str = pydantic.Field(default=None, pattern="^#[0-9a-fA-F]{6}$")
    accent: str = pydantic.Field(default=None, pattern="^#[0-9a-fA-F]{6}$")
    background: str = pydantic.Field(default=None, pattern="^#[0-9a-fA-F]{6}$")
    surface: str = pydantic.Field(default=None, pattern="^#[0-9a-fA-F]{6}$")
    panel: str = pydantic.Field(default=None, pattern="^#[0-9a-fA-F]{6}$")


class Sound(pydantic.BaseModel):
    """Class for sounds."""
    text: typing.Optional[str] = None
    emoji: typing.Optional[str] = None  # trying to match emojis isn't worth it


class Config(pydantic.BaseModel):
    """Class for storing the configuration."""
    language: str = pydantic.Field(pattern="^[a-z]{3}$")  # close enough
    show_clock: bool
    default_emoji: str
    audio_path: pydantic.DirectoryPath
    language_path: pydantic.DirectoryPath
    styles_path: pydantic.DirectoryPath
    themes_path: pydantic.FilePath
    theme: str
    style: str
    sounds: dict[str, Sound]

    @property
    def style_path(self) -> pathlib.Path:
        """Style path computated field."""
        return pathlib.Path(self.styles_path, f"{self.style}.tcss")

    @classmethod
    def load(cls) -> "Config":
        """Load the config from file."""
        return Config.model_validate_json(pathlib.Path(CONFIG_PATH).read_text("utf-8"))

    def save(self) -> None:
        """Save the config to file."""
        config_json: str = self.model_dump_json(exclude_defaults=True)
        pathlib.Path(CONFIG_PATH).write_text(config_json, "utf-8")


# maybe?
CONFIG = Config.load()


def load_languages() -> dict[str, dict[str, str]]:
    """Load the language file for the provided language.
    TODO: improve
    Should be a ISO 639-2 code but technically is just the name of a JSON file.

    Arguments:
        - lang_code: language to load.

    Returns:
        The text for the language as a dict.

    Raises:
        FileNotFoundError if no language file can be found.
    """
    lang_maps: dict[str, dict[str, str]] = {}
    for file in pathlib.Path(CONFIG.language_path).iterdir():
        lang_maps[file.name.removesuffix(".json")] = json.loads(
            file.read_text("utf-8"))
        # TODO: maybe verify?
    return lang_maps


def load_themes() -> dict[str, textual.design.ColorSystem]:
    """Load all themes (textual color systems).

    Returns:
        The themes.
    """
    # well, it works
    # TODO: improve
    results = {}
    colors: list[dict[str, typing.Any]] = json.loads(
        pathlib.Path(CONFIG.themes_path).read_text("utf-8"))
    for color in colors:
        color_name = color["name"]
        color.pop("name")
        # currently not needed
        color.pop("description", None)
        color_system = textual.design.ColorSystem(**color)
        results[color_name] = color_system
    return results


class Text:
    """Class for translatable text."""
    lang_maps: dict[str, dict[str, str]] = load_languages()

    @staticmethod
    def translatable(key: str, **format_args: typing.Any) -> str:
        """Get translated text if available.

        Arguments:
            - key: key to look for.
            - **format_args: allows optional arguments for formatting.

        Returns:
            The text if it exists, key otherwise.
        """
        if Text.lang_maps.get(CONFIG.language) is not None \
                and Text.lang_maps[CONFIG.language].get(key) is not None:
            return Text.lang_maps[CONFIG.language][key].format_map(format_args)
        return key
