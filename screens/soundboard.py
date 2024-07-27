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

    state: int = 0

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        yield textual.widgets.Header(show_clock=util.CONFIG.show_clock)
        with textual.containers.ScrollableContainer(id="buttons"):
            for entry in pathlib.Path(util.CONFIG.audio_path).iterdir():
                if entry.is_file() and entry.suffix in FILE_TYPES:
                    yield widgets.sound_button.SoundButton(file=entry)
        yield textual.widgets.Footer()

    def action_toggle_text(self) -> None:
        """Toggle the text."""
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
            # needed to reload css and correctly change button height
            button.refresh(layout=True)

    def action_reload(self) -> None:
        """Reload the soundboard screen."""
        # FIXME: reload all screens; maybe automatically?
        self.app.pop_screen()
        self.app.push_screen("soundboard")
        self.notify(message=util.Text.translatable("notification.reload.msg"),
                    title=util.Text.translatable("notification.reload.title"),
                    severity="information")
