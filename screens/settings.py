"""Settings screen."""

import pathlib
import typing

import textual.app
import textual.containers
import textual.screen
import textual.widgets

import screens.soundboard
import utils.config
import utils.translate


class ExitScreen(textual.screen.ModalScreen):
    """Exit modal screen."""

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        with textual.containers.Grid(id="dialogue"):
            yield textual.widgets.Label(utils.translate.Text.translatable("exit.question"),
                                        id="question")
            yield textual.widgets.Button(utils.translate.Text.translatable("exit.yes"),
                                         id="yes", variant="success")
            yield textual.widgets.Button(utils.translate.Text.translatable("exit.no"),
                                         id="no", variant="error")

    @textual.on(textual.widgets.Button.Pressed, "#yes")
    def pressed_quit(self, event: textual.widgets.Button.Pressed) -> None:
        """Handle button pressed event for quit."""
        event.stop()
        utils.config.CONFIG.store()
        self.app.exit()

    @textual.on(textual.widgets.Button.Pressed, "#no")
    def pressed_cancel(self, event: textual.widgets.Button.Pressed) -> None:
        """Handle button pressed event for cancel."""
        event.stop()
        self.app.pop_screen()


class SettingsScreen(textual.screen.Screen):
    """Class for the settings screen."""
    TITLE = utils.translate.Text.translatable("settings.header")
    BINDINGS = [
        ("s", "close", utils.translate.Text.translatable("settings.footer.close"))
    ]

    audio_device_changed: bool

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        languages: list[tuple[str, str]] = []
        for file in pathlib.Path("lang").iterdir():
            name: str = file.stem
            languages.append((name, name))
        yield textual.widgets.Header(show_clock=utils.config.CONFIG.show_clock)
        with textual.containers.Grid(id="config"):
            with textual.containers.Center():
                yield textual.widgets.Label(utils.translate.Text.translatable(
                    "settings.language.title"), classes="config_label")
            with textual.containers.Center():
                yield textual.widgets.Select(languages, allow_blank=False,
                                             value=utils.config.CONFIG.language,
                                             id="language_select", classes="config_option")
            with textual.containers.Center():
                yield textual.widgets.Label(utils.translate.Text.translatable(
                    "settings.clock.title"), classes="config_label")
            with textual.containers.Center():
                yield textual.widgets.Switch(value=utils.config.CONFIG.show_clock,
                                             id="clock_switch", classes="config_option")
            with textual.containers.Center():
                yield textual.widgets.Label(utils.translate.Text.translatable(
                    "settings.emoji.title"), classes="config_label")
            with textual.containers.Center():
                yield textual.widgets.Input(utils.config.CONFIG.default_emoji,
                                            id="emoji_input", classes="config_option")
            with textual.containers.Center():
                yield textual.widgets.Label(utils.translate.Text.translatable(
                    "settings.theme.title"), classes="config_label")
            with textual.containers.Center():
                yield textual.widgets.Select([(theme, theme)
                                              for theme in self.app.available_themes],
                                             allow_blank=False, value=self.app.theme,
                                             id="theme_select", classes="config_option")
            with textual.containers.Center():
                yield textual.widgets.Label(utils.translate.Text.translatable(
                    "settings.input.title"), classes="config_label")
            with textual.containers.Center():
                yield textual.widgets.Select([(device[0], index) for index, device
                                              in utils.config.get_input_devices().items()],
                                             allow_blank=False,
                                             value=utils.config.CONFIG.input_device,
                                             id="input_select", classes="config_option")
            with textual.containers.Center():
                yield textual.widgets.Label(utils.translate.Text.translatable(
                    "settings.output.title"), classes="config_label")
            with textual.containers.Center():
                yield textual.widgets.Select([(device[0], index) for index, device
                                              in utils.config.get_output_devices().items()],
                                             allow_blank=False,
                                             value=utils.config.CONFIG.output_device,
                                             id="output_select", classes="config_option")
            with textual.containers.Center():
                yield textual.widgets.Label(utils.translate.Text.translatable(
                    "settings.virtual.title"), classes="config_label")
            with textual.containers.Center():
                yield textual.widgets.Select([(device[0], index) for index, device
                                              in utils.config.get_output_devices().items()],
                                             allow_blank=False,
                                             value=utils.config.CONFIG.virtual_output_device,
                                             id="virtual_select", classes="config_option")
        yield textual.widgets.Footer()

    def on_show(self) -> None:
        """Do stuff on show."""
        self.audio_device_changed: bool = False

    def action_close(self) -> None:
        """Handle close action."""
        if self.audio_device_changed:
            self.app.push_screen(ExitScreen())
        else:
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

    @textual.on(textual.widgets.Select.Changed, "#input_select")
    def choose_input(self, event: textual.widgets.Select.Changed) -> None:
        """Choose the input."""
        event.stop()
        self.audio_device_changed = True
        utils.config.CONFIG.input_device = typing.cast(int, event.value)

    @textual.on(textual.widgets.Select.Changed, "#output_select")
    def choose_output(self, event: textual.widgets.Select.Changed) -> None:
        """Choose the output."""
        event.stop()
        self.audio_device_changed = True
        utils.config.CONFIG.output_device = typing.cast(int, event.value)

    @textual.on(textual.widgets.Select.Changed, "#virtual_select")
    def choose_virtual(self, event: textual.widgets.Select.Changed) -> None:
        """Choose the virtual."""
        self.audio_device_changed = True
        utils.config.CONFIG.virtual_output_device = typing.cast(
            int, event.value)
