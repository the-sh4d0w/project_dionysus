"""Util stuff."""
import json
import pathlib
import typing

import pydantic
import pydantic.validators


def load_language(lang_code: str) -> dict[str, str]:
    """Loads the language file for the provided language.
    Should be a ISO 639-2 code but technically is just the name of a JSON file.

    Arguments:
        - lang_code: language to load.

    Returns:
        The text for the language as a dict.

    Raises:
        FileNotFoundError: if no language file can be found.
    """
    path = pathlib.Path(Config.config.language_path, f"{lang_code}.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError("the specified language does not exist")


def get_themes() -> dict[str, "Theme"]:
    """Get all themes.

    Returns:
        A list of all themes.
    """
    themes_list = pydantic.TypeAdapter(list[Theme]).validate_json(
        pathlib.Path(Config.config.themes_path, "themes.json").read_text(encoding="utf-8"))
    return {theme.name: theme for theme in themes_list}


class Color(pydantic.BaseModel):
    """Class for colors."""
    name: str
    primary: str = pydantic.Field(pattern="^#[a-fA-F0-9]{6}$")
    secondary: str = pydantic.Field(pattern="^#[a-fA-F0-9]{6}$")
    backgound: str = pydantic.Field(pattern="^#[a-fA-F0-9]{6}$",
                                    default="#000000")


class Theme(pydantic.BaseModel):
    """Class for themes."""
    name: str = ""
    colors: dict[str, Color]

    @pydantic.field_validator("colors", mode="before")
    @classmethod
    def dict_to_color(cls, data: dict) -> dict[str, Color]:
        """Turn a dict into a Color."""
        if not isinstance(data, dict):
            return data
        name, colors = data.popitem()
        return {name: Color(name=name, **colors)}


class Sound(pydantic.BaseModel):
    """Class for sounds."""
    text: typing.Optional[str] = None
    emoji: typing.Optional[str] = None  # trying to match emojis isn't worth it


class Configuration(pydantic.BaseModel):
    """Class for storing the configuration."""
    language: str = pydantic.Field(pattern="^[a-z]{3}$")  # close enough
    theme_name: str = pydantic.Field(exclude=True)
    color_name: str = pydantic.Field(exclude=True)
    show_clock: bool
    default_emoji: str
    audio_path: pydantic.DirectoryPath
    language_path: pydantic.DirectoryPath
    themes_path: pydantic.DirectoryPath
    sounds: dict[str, Sound]

    @pydantic.computed_field
    @property
    def theme(self) -> Theme:
        """Property for theme."""
        # FIXME: probably with a field validator
        return get_themes()["classic"]

    @pydantic.computed_field
    @property
    def color(self) -> Color:
        """Property for color."""
        # FIXME: probably also with a field validator
        return get_themes()["classic"].colors["classic"]


class Config:
    """Class for handling the config."""
    config_path = pathlib.Path("config.json")
    config = Configuration.model_validate_json(
        config_path.read_text(encoding="utf-8"))

    @staticmethod
    def load() -> None:
        """Load the config from the file."""
        Config.config = Configuration.model_validate_json(
            Config.config_path.read_text(encoding="utf-8"))

    @staticmethod
    def save() -> None:
        """Save the config to the file."""
        Config.config_path.write_text(Config.config.model_dump_json(
            exclude_defaults=True), encoding="utf-8")


class Text:
    """Class for translatable text."""
    lang_code: str = Config.config.language
    lang_map: dict[str, str] = load_language(lang_code)

    @staticmethod
    def set_language(code: str) -> None:
        """Set the language to use.

        Arguments:
            - code: ISO 639-2 code of the language to load.
        """
        Text.lang_map = load_language(code)
        Text.lang_code = code

    @staticmethod
    def translatable(key: str, **format_args: typing.Any) -> str:
        """Get translated text if available.

        Arguments:
            - key: key to look for.
            - **format_args: allows optional arguments for formatting.

        Returns:
            The text if it exists, key otherwise.
        """
        return Text.lang_map[key].format_map(format_args) \
            if Text.lang_map.get(key) is not None else key
