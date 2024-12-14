"""Soundboard screen."""

import pathlib
import typing

import textual.app
import textual.containers
import textual.css
import textual.screen
import textual.widgets

import screens.settings
import screens.help
import utils.config
import utils.translate
import widgets.sound_button


FILE_TYPES = (".mp3", ".wav", ".ogg")
AUDIO_PATH = "audio/"


class SoundboardScreen(textual.screen.Screen):
    """Class for the soundboard screen."""
    TITLE =  utils.translate.Text.translatable("soundboard.header")
    BINDINGS = [
        ("q", "quit",
         utils.translate.Text.translatable("soundboard.footer.quit")),
        ("s", "settings",
         utils.translate.Text.translatable("soundboard.footer.settings")),
        ("h", "help",
         utils.translate.Text.translatable("soundboard.footer.help")),
        ("t", "toggle_text",
         utils.translate.Text.translatable("soundboard.footer.toggle"))
    ]

    state: int = 0

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        yield textual.widgets.Header(show_clock=utils.config.CONFIG.show_clock)
        with textual.containers.ScrollableContainer(id="buttons"):
            for entry in pathlib.Path(AUDIO_PATH).iterdir():
                if entry.is_file() and entry.suffix in FILE_TYPES:
                    yield widgets.sound_button.SoundButton(file=entry)
        yield textual.widgets.Footer()

    def action_quit(self) -> None:
        """Handle quit action."""
        self.app.exit()

    def action_settings(self) -> None:
        """Handle settings action."""
        self.app.pop_screen()
        self.app.push_screen(screens.settings.SettingsScreen())

    def action_help(self) -> None:
        """Handle help action."""
        self.app.pop_screen()
        self.app.push_screen(screens.help.HelpScreen())

    def action_toggle_text(self) -> None:
        """Handle toggle_text action."""
        container: textual.containers.ScrollableContainer = typing.cast(
            textual.containers.ScrollableContainer, self.query_one("#buttons"))
        self.state = (self.state + 1) % 3
        for button in self.query(".sound-button").results(
                widgets.sound_button.SoundButton):
            match self.state:
                case 0:
                    container.styles.grid_size_columns = 5
                    button.label = f"{button.emoji}\n{button.text}"
                case 1:
                    container.styles.grid_size_columns = 10
                    button.label = button.emoji
                case 2:
                    container.styles.grid_size_columns = 5
                    button.label = button.text
        self.app.refresh_css()
