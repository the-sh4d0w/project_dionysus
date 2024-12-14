"""Translatable text."""

import json
import pathlib
import typing

import utils.config


def load_languages() -> dict[str, dict[str, str]]:
    """Load all language files.

    Returns:
        The text for all languages as dicts.
    """
    lang_maps: dict[str, dict[str, str]] = {}
    for file in pathlib.Path("lang").iterdir():
        lang_maps[file.name.removesuffix(".json")] = json.loads(
            file.read_text("utf-8"))
    return lang_maps


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
        if Text.lang_maps.get(utils.config.CONFIG.language) is not None \
                and Text.lang_maps[utils.config.CONFIG.language].get(key) is not None:
            return Text.lang_maps[utils.config.CONFIG.language][key].format_map(format_args)
        return key
