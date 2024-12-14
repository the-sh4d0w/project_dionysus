"""Settings screen."""

import pathlib

import textual.app
import textual.containers
import textual.screen
import textual.widgets

import screens.soundboard
import utils.config
import utils.translate


class SettingsScreen(textual.screen.Screen):
    """Class for the settings screen."""
    TITLE = "Dionysus - Config"
    BINDINGS = [
        ("s", "close", utils.translate.Text.translatable("config.footer.close"))
    ]

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        languages: list[tuple[str, str]] = []
        for file in pathlib.Path("lang").iterdir():
            name: str = file.stem
            languages.append((name, name))
        yield textual.widgets.Header(show_clock=utils.config.CONFIG.show_clock)
        with textual.containers.Vertical(id="config"):
            with textual.containers.Horizontal():
                yield textual.widgets.Label(utils.translate.Text.translatable(
                    "config.language.title"), classes="config_label")
                yield textual.widgets.Select(languages, allow_blank=False,
                                             value=utils.config.CONFIG.language,
                                             id="language_select", classes="config_option")
            with textual.containers.Horizontal():
                yield textual.widgets.Label(utils.translate.Text.translatable(
                    "config.clock.title"), classes="config_label")
                yield textual.widgets.Switch(utils.config.CONFIG.show_clock,
                                             id="clock_switch", classes="config_option")
            with textual.containers.Horizontal():
                yield textual.widgets.Label(utils.translate.Text.translatable(
                    "config.emoji.title"), classes="config_label")
                yield textual.widgets.Input(utils.config.CONFIG.default_emoji,
                                            id="emoji_input", classes="config_option")
            with textual.containers.Horizontal():
                yield textual.widgets.Label(utils.translate.Text.translatable(
                    "config.theme.title"), classes="config_label")
                yield textual.widgets.Select([(theme, theme)
                                              for theme in self.app.available_themes],
                                             allow_blank=False, value=self.app.theme,
                                             id="theme_select", classes="config_option")
        yield textual.widgets.Footer()

    def action_close(self) -> None:
        """Handle close action."""
        utils.config.CONFIG.store()
        self.app.pop_screen()
        self.app.push_screen(screens.soundboard.SoundboardScreen())

    @textual.on(textual.widgets.Select.Changed, "#language_select")
    def choose_langauge(self, event: textual.widgets.Select.Changed) -> None:
        """Choose the language."""
        event.stop()
        utils.config.CONFIG.language = str(event.value)

    @textual.on(textual.widgets.Switch.Changed, "#clock_switch")
    def set_clock(self, event: textual.widgets.Switch.Changed) -> None:
        """Set the clock."""
        event.stop()
        utils.config.CONFIG.show_clock = event.value

    @textual.on(textual.widgets.Input.Changed, "#emoji_input")
    def choose_emoji(self, event: textual.widgets.Input.Changed) -> None:
        """Choose the emoji."""
        event.stop()
        utils.config.CONFIG.default_emoji = event.value

    @textual.on(textual.widgets.Select.Changed, "#theme_select")
    def choose_theme(self, event: textual.widgets.Select.Changed) -> None:
        """Choose the theme."""
        event.stop()
        self.app.theme = str(  # pylint:disable=attribute-defined-outside-init
            event.value)
        utils.config.CONFIG.theme = str(event.value)
