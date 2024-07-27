"""Config screen."""

import pathlib

import textual.app
import textual.containers
import textual.screen
import textual.widgets

import util


class ConfigScreen(textual.screen.Screen):
    """Class for the config screen."""
    # needed because of how select works
    lang_select_first = True
    theme_select_first = True
    TITLE = "Dionysus - Config"
    BINDINGS = [
        ("q", "app.quit()", util.Text.translatable("soundboard.footer.quit")),
        ("c", "app.switch_screen('soundboard')",
         util.Text.translatable("config.footer.close"))
    ]

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        languages: list[tuple[str, str]] = []
        for file in pathlib.Path(util.CONFIG.language_path).iterdir():
            name: str = file.stem
            languages.append((name, name))
        yield textual.widgets.Header(show_clock=util.CONFIG.show_clock)
        with textual.containers.Vertical():
            with textual.containers.Horizontal(id="theme", classes="config"):
                # FIXME: implement this correctly
                yield textual.widgets.Select([("classic", "classic")],
                                             allow_blank=False, id="theme_select")
                yield textual.widgets.Select([("red", 1), ("blue", 1), ("green", 3)],
                                             allow_blank=False, id="color_select")
            with textual.containers.Container(id="language", classes="config"):
                yield textual.widgets.Select(languages, allow_blank=False,
                                             value=util.CONFIG.language, id="language_select")
            with textual.containers.Container(id="clock", classes="config"):
                yield textual.widgets.Switch(util.CONFIG.show_clock)
            with textual.containers.Container(id="emoji", classes="config"):
                yield textual.widgets.Input(util.CONFIG.default_emoji,
                                            id="emoji_input")
        yield textual.widgets.Footer()

    def on_mount(self) -> None:
        """Add titles on mount."""
        self.query_one("#theme").border_title = util.Text.translatable(
            "config.theme.title")
        self.query_one("#language").border_title = util.Text.translatable(
            "config.language.title")
        self.query_one("#clock").border_title = util.Text.translatable(
            "config.language.title")
        self.query_one("#emoji").border_title = util.Text.translatable(
            "config.emoji.title")

    @textual.on(textual.widgets.Select.Changed, "#theme_select")
    def set_colors(self, event: textual.widgets.Select.Changed) -> None:
        """Set the correct color choices for a theme."""
        # FIXME: implement this

    @textual.on(textual.widgets.Select.Changed, "#language_select")
    def choose_langauge(self, event: textual.widgets.Select.Changed) -> None:
        """Set the correct color choices for a theme."""
        # FIXME: implement this correctly
        util.CONFIG.language = str(event.value)

    @textual.on(textual.widgets.Switch.Changed)
    def set_clock(self, event: textual.widgets.Switch.Changed) -> None:
        """Set the show clock value."""
        util.CONFIG.show_clock = event.value

    @textual.on(textual.widgets.Input.Changed, "#emoji_input")
    def choose_emoji(self, event: textual.widgets.Input.Changed) -> None:
        """Choose the default emoji."""
        util.CONFIG.default_emoji = event.value
