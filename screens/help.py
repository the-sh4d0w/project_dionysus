"""Help screen."""

import textual.app
import textual.containers
import textual.screen
import textual.widgets

import screens.soundboard
import utils.config
import utils.translate


class HelpScreen(textual.screen.Screen):
    """Class for the help screen."""
    TITLE = "Dionysus - Help"
    BINDINGS = [
        ("h", "close", utils.translate.Text.translatable("help.footer.close"))
    ]

    def action_close(self) -> None:
        """Handle close action."""
        self.app.pop_screen()
        self.app.push_screen(screens.soundboard.SoundboardScreen())

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        yield textual.widgets.Header(show_clock=utils.config.CONFIG.show_clock)
        with textual.containers.Vertical(id="help"):
            with textual.containers.Vertical(classes="faq"):
                yield textual.widgets.Static(utils.translate.Text.translatable(
                    "help.file_question"), classes="title")
                yield textual.widgets.Static(utils.translate.Text.translatable(
                    "help.file_text", AUDIO_PATH=screens.soundboard.AUDIO_PATH), classes="text")
            with textual.containers.Vertical(classes="faq"):
                yield textual.widgets.Static(utils.translate.Text.translatable(
                    "help.icon_question"), classes="title")
                yield textual.widgets.Static(utils.translate.Text.translatable(
                    "help.icon_text", SOUNDS_PATH=utils.config.SOUNDS_PATH), classes="text")
            with textual.containers.Vertical(classes="faq"):
                yield textual.widgets.Static(utils.translate.Text.translatable(
                    "help.name_question"), classes="title")
                yield textual.widgets.Static(utils.translate.Text.translatable(
                    "help.name_text", SOUNDS_PATH=utils.config.SOUNDS_PATH), classes="text")
            with textual.containers.Vertical(classes="faq"):
                yield textual.widgets.Static(utils.translate.Text.translatable(
                    "help.sound_question"), classes="title")
                yield textual.widgets.Static(utils.translate.Text.translatable(
                    "help.sound_text"), classes="text")
            with textual.containers.Vertical(classes="faq"):
                yield textual.widgets.Static(utils.translate.Text.translatable(
                    "help.json_question"), classes="title")
                yield textual.widgets.Static(utils.translate.Text.translatable(
                    "help.json_text"), classes="text")
        yield textual.widgets.Footer()
