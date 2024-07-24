"""Soundboard screen."""

import pathlib
import typing

import textual.app
import textual.containers
import textual.css
import textual.screen
import textual.widgets

import util
import widgets.sound_button


FILE_TYPES = (".mp3", ".wav", ".ogg")


class SoundboardScreen(textual.screen.Screen):
    """Class for the soundboard screen."""
    TITLE = "Dionysus - Soundboard"
    BINDINGS = [
        ("q", "app.quit()", util.Text.translatable("soundboard.footer.quit")),
        ("c", "app.switch_screen('config')",
         util.Text.translatable("soundboard.footer.config")),
        ("h", "app.switch_screen('help')",
         util.Text.translatable("soundboard.footer.open")),
        ("t", "toggle_text()", util.Text.translatable("soundboard.footer.toggle")),
        ("r", "reload()", util.Text.translatable("soundboard.footer.reload"))
    ]

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        yield textual.widgets.Header(show_clock=util.Config.config.show_clock)
        with textual.containers.ScrollableContainer(id="buttons"):
            for entry in pathlib.Path(util.Config.config.audio_path).iterdir():
                if entry.is_file() and entry.suffix in FILE_TYPES:
                    yield widgets.sound_button.SoundButton(file=entry)
        yield textual.widgets.Footer()

    def action_toggle_text(self) -> None:
        """Toggle the text."""
        button: widgets.sound_button.SoundButton
        container: textual.containers.ScrollableContainer = typing.cast(
            textual.containers.ScrollableContainer, self.query_one("#buttons"))
        for button in self.query(".sound-button").results(
                widgets.sound_button.SoundButton):
            if str(button.label) == button.emoji:
                container.styles.grid_size_columns = 5
                button.label = f"{button.emoji} {button.text}"
            elif str(button.label) == button.text:
                container.styles.grid_size_columns = 10
                button.label = button.emoji
            else:
                container.styles.grid_size_columns = 5
                button.label = button.text

    def action_reload(self) -> None:
        """Reload the config and sound buttons."""
        # FIXME: circular import; can probably easily remove
        # self.app: SoundboardApp
        self.app.reload()
