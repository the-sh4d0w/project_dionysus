"""Help screen."""

import textual.app
import textual.containers
import textual.screen
import textual.widgets

import util
import widgets.faq


class HelpScreen(textual.screen.Screen):
    """Class for the help screen."""
    TITLE = "Dionysus - Help"
    BINDINGS = [
        ("q", "app.quit()", util.Text.translatable("soundboard.footer.quit")),
        ("h", "app.switch_screen('soundboard')",
         util.Text.translatable("help.footer.close"))
    ]

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        yield textual.widgets.Header(show_clock=util.Config.config.show_clock)
        with textual.containers.Container(id="help"):
            yield widgets.faq.FAQ(title=util.Text.translatable("help.file_question"),
                                  text=util.Text.translatable("help.file_text",
                                                              AUDIO_PATH=util.Config.config.audio_path))
            yield widgets.faq.FAQ(title=util.Text.translatable("help.icon_question"),
                                  text=util.Text.translatable("help.icon_text",
                                                              CONFIG_PATH=util.Config.config_path))
            yield widgets.faq.FAQ(title=util.Text.translatable("help.name_question"),
                                  text=util.Text.translatable("help.name_text",
                                                              CONFIG_PATH=util.Config.config_path))
            yield widgets.faq.FAQ(title=util.Text.translatable("help.sound_question"),
                                  text=util.Text.translatable("help.sound_text"))
            yield widgets.faq.FAQ(title=util.Text.translatable("help.json_question"),
                                  text=util.Text.translatable("help.json_text"))
        yield textual.widgets.Footer()
