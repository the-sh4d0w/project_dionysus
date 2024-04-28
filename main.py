"""Main file for Project Dionysus, a soundboard."""

# TODO:
# - fix text being cut off (button and help)
# - maybe move more stuff into config
# - themes! -> color selection; theme selection
# - better options menu
# -> language
# -> theme/colors
# -> file/folder locations? -> multiple audio folders
# -> select input/output device
# -> default emoji
# - maybe reloading text without restart (destroy screen?)
# - use os.path to handle file paths (or pathlib)
# - translate
# - structure project
# - add logging (even if only through textual console)

import os
import pathlib
import threading
import queue
import typing

import numpy
import sounddevice
import soundfile
import textual
import textual.app
import textual.color
import textual.containers
import textual.css.query
import textual.css.stylesheet
import textual.screen
import textual.widgets

import util

DEVICE_NAME = "CABLE Input MME"  # somehow matches correct device
FILE_TYPES = (".mp3", ".wav", ".ogg")


class NoCableError(Exception):
    """Error to raise if VB-Audio Virtual Cable is not correctly installed."""


def get_devices() -> tuple[int, int, int]:
    """Get all devices.

    Returns:
        The default input, default output and CABLE Input device ids.
    """
    try:
        return *typing.cast(tuple[int, int], sounddevice.default.device), \
            typing.cast(dict[str, int], sounddevice.query_devices(
                DEVICE_NAME))["index"]
    except ValueError as exc:
        raise NoCableError(
            "you don't have VB-Audio Virtual Cable installed") from exc


def audio_thread(audio_queue: queue.Queue, device: int) -> None:
    """Function for local audio output thread.

    Arguments:
        - audio_queue: queue to get audio data from.
        - device: the id of the playback device.
    """
    while True:
        if data := audio_queue.get():
            audio_data, samplerate = data
            sounddevice.play(data=audio_data, samplerate=samplerate,
                             device=device, blocking=True)
        else:
            break


def callback(indata: numpy.ndarray, outdata: numpy.ndarray,
             frames, time, status) -> None:  # pylint: disable=unused-argument
    """Callback function. The type of time should actually be CData."""
    outdata[:] = indata


class FAQ(textual.containers.Container):
    """Class for FAQ entries."""

    def __init__(self, title: str, text: str) -> None:
        """Initialize the FAQ."""
        super().__init__(classes="entry")
        self.title = title
        self.text = text

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        yield textual.widgets.Static(renderable=self.title, classes="title")
        yield textual.widgets.Static(renderable=self.text, classes="text")


class SoundButton(textual.widgets.Button):
    """Class for custom sound button."""

    def __init__(self, file: pathlib.Path) -> None:
        """Initialize the button.

        Arguments:
            - file: path of the sound file.
        """
        self.file = file
        self.text = file.stem
        self.emoji = util.Config.config.default_emoji
        file_name = file.stem + file.suffix
        if util.Config.config.sounds.get(file_name):
            if util.Config.config.sounds[file_name].text:
                self.text = str(util.Config.config.sounds[file_name].text)
            textual.log(self.text)
            if util.Config.config.sounds[file_name].emoji:
                self.emoji = str(util.Config.config.sounds[file_name].emoji)
        super().__init__(label=f"{self.emoji} {self.text}",
                         classes="sound-button")
        self.tooltip = self.text

    def press(self) -> None:
        """Do something when button is pressed."""
        try:
            self.app: SoundboardApp
            data, samplerate = soundfile.read(file=self.file)
            self.app.local_queue.put((data, samplerate))
            self.app.cable_queue.put((data, samplerate))
        except soundfile.LibsndfileError as exc:
            self.app.notify(message=exc.error_string,
                            title=exc.prefix.removesuffix(": "),
                            severity="error")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.app.notify(message=str(exc), title="Something went wrong",
                            severity="warning")


class ExitScreen(textual.screen.ModalScreen[str]):
    """Class for the exit modal screen."""

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        yield textual.containers.Grid(
            textual.widgets.Label("You need to restart to apply changes.\nDo you want to exit?",
                                  id="question"),
            textual.widgets.Button("Quit", id="quit"),
            textual.widgets.Button("Cancel", id="cancel"),
            id="dialog"
        )

    def on_button_pressed(self, event: textual.widgets.Button.Pressed) -> None:
        """Something on button pressed."""
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()


class SoundboardScreen(textual.screen.Screen):
    """Class for the soundboard screen."""
    TITLE = "Dionysus - Soundboard"
    BINDINGS = [
        ("q", "quit()", util.Text.translatable("soundboard.footer.quit")),
        ("c", "switch_screen('config')",
         util.Text.translatable("soundboard.footer.config")),
        ("h", "switch_screen('help')",
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
                    yield SoundButton(file=entry)
        yield textual.widgets.Footer()

    def action_toggle_text(self) -> None:
        """Toggle the text."""
        button: SoundButton
        container: textual.containers.ScrollableContainer = typing.cast(
            textual.containers.ScrollableContainer, self.query_one("#buttons"))
        for button in typing.cast(textual.css.query.DOMQuery[SoundButton],  # pylint: disable=not-an-iterable
                                  self.query(".sound-button")):
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
        self.app: SoundboardApp
        self.app.reload()


class ConfigScreen(textual.screen.Screen):
    """Class for the config screen."""
    # needed because of how select works
    lang_select = 0
    theme_selct = 0
    TITLE = "Dionysus - Config"
    BINDINGS = [
        ("q", "quit()", util.Text.translatable("soundboard.footer.quit")),
        ("c", "switch_screen('soundboard')",
         util.Text.translatable("config.footer.close"))
    ]

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        languages: list[tuple[str, str]] = []
        # FIXME: use pathlib
        for file in os.listdir(util.Config.config.language_path):
            name: str = pathlib.Path(file).stem
            languages.append((name, name))
        yield textual.widgets.Header(show_clock=util.Config.config.show_clock)
        with textual.containers.Vertical():
            with textual.containers.Horizontal(id="theme", classes="config"):
                # FIXME: implement this correctly
                yield textual.widgets.Select([(theme.name, theme.name)
                                              for theme in util.get_themes().values()],
                                             allow_blank=False, id="theme_select")
                yield textual.widgets.Select([("red", 1), ("blue", 1), ("green", 3)],
                                             allow_blank=False, id="color_select")
            with textual.containers.Container(id="language", classes="config"):
                yield textual.widgets.Select(languages, allow_blank=False,
                                             value=util.Text.lang_code, id="language_select")
            with textual.containers.Container(classes="config"):
                yield textual.widgets.Switch(util.Config.config.show_clock)
        yield textual.widgets.Footer()

    def on_mount(self) -> None:
        """Add titles on mount."""
        self.query_one("#theme").border_title = "Theme"
        self.query_one("#language").border_title = "Language"

    @textual.on(textual.widgets.Select.Changed, "#theme_select")
    def set_colors(self, event: textual.widgets.Select.Changed) -> None:
        """Set the correct color choices for a theme."""
        # FIXME: implement this correctly
        if ConfigScreen.theme_selct > 0:
            color_select = typing.cast(
                textual.widgets.Select, self.query_one("#color_select"))
            # color_select.set_options(event.select._options)
        ConfigScreen.theme_selct += 1

    @textual.on(textual.widgets.Select.Changed, "#language_select")
    def choose_langauge(self, event: textual.widgets.Select.Changed) -> None:
        """Set the correct color choices for a theme."""
        # FIXME: implement this correctly
        lang = str(event.value)
        if ConfigScreen.lang_select > 0:
            self.app.push_screen(ExitScreen())
        ConfigScreen.lang_select += 1


class HelpScreen(textual.screen.Screen):
    """Class for the help screen."""
    TITLE = "Dionysus - Help"
    BINDINGS = [
        ("q", "quit()", util.Text.translatable("soundboard.footer.quit")),
        ("h", "switch_screen('soundboard')",
         util.Text.translatable("help.footer.close"))
    ]

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        self.app: SoundboardApp
        yield textual.widgets.Header(show_clock=util.Config.config.show_clock)
        with textual.containers.Container(id="help"):
            yield FAQ(title=util.Text.translatable("help.file_question"),
                      text=util.Text.translatable("help.file_text",
                                                  AUDIO_PATH=util.Config.config.audio_path))
            yield FAQ(title=util.Text.translatable("help.icon_question"),
                      text=util.Text.translatable("help.icon_text",
                                                  CONFIG_PATH=util.Config.config_path))
            yield FAQ(title=util.Text.translatable("help.name_question"),
                      text=util.Text.translatable("help.name_text",
                                                  CONFIG_PATH=util.Config.config_path))
            yield FAQ(title=util.Text.translatable("help.sound_question"),
                      text=util.Text.translatable("help.sound_text"))
            yield FAQ(title=util.Text.translatable("help.json_question"),
                      text=util.Text.translatable("help.json_text"))
        yield textual.widgets.Footer()


class SoundboardApp(textual.app.App):
    """Class for the app."""
    CSS_PATH = pathlib.Path(util.Config.config.themes_path, "simple.tcss")
    TITLE = "Dionysus"

    def __init__(self, local_queue: queue.Queue, cable_queue: queue.Queue,
                 lang: str = "eng") -> None:
        """Initialize the soundboard app."""
        super().__init__()
        self.local_queue = local_queue
        self.cable_queue = cable_queue
        # update theme for the first time
        self.update_theme()

    def on_mount(self) -> None:
        """Install screens on mount."""
        self.install_screen(SoundboardScreen(), "soundboard")
        self.install_screen(HelpScreen(), "help")
        self.install_screen(ConfigScreen(), "config")
        self.push_screen("soundboard")

    def reload(self) -> None:
        """Reload the config."""
        self.pop_screen()
        self.uninstall_screen("soundboard")
        self.install_screen(SoundboardScreen(), "soundboard")
        self.push_screen("soundboard")
        self.notify(message=util.Text.translatable("notification.reload.msg"),
                    title=util.Text.translatable("notification.reload.title"),
                    severity="information")

    def update_theme(self) -> None:
        """Update the theme."""
        variables = self.get_css_variables()
        color = typing.cast(util.Color, util.Config.config.color)
        primary_color = textual.color.Color.parse(color.primary)
        secondary_color = textual.color.Color.parse(color.secondary)
        variables["theme_primary"] = primary_color.hex
        variables["theme_secondary"] = secondary_color.hex
        for i in range(1, 4):
            # primary
            variables[f"theme_primary-darken-{i}"] = primary_color.darken(
                i * 15 / 100).hex
            variables[f"theme_primary-lighten-{i}"] = primary_color.lighten(
                i * 15 / 100).hex
            # secondary
            variables[f"theme_secondary-darken-{i}"] = secondary_color.darken(
                i * 15 / 100).hex
            variables[f"theme_secondary-lighten-{i}"] = secondary_color.lighten(
                i * 15 / 100).hex
        self.stylesheet.set_variables(variables)
        self.stylesheet.reparse()
        self.stylesheet.update(self.app)

    async def action_quit(self) -> None:
        """Quit the app and save the config."""
        # FIXME: writes theme and color to config, shouldn't
        # util.Config.save()
        await super().action_quit()


if __name__ == "__main__":
    default_in, default_out, cable = get_devices()
    local_audio_queue = queue.Queue()
    cable_audio_queue = queue.Queue()
    threading.Thread(target=audio_thread,
                     args=(local_audio_queue, default_out)).start()
    threading.Thread(target=audio_thread,
                     args=(cable_audio_queue, cable)).start()
    # should alway be 2 channels (probably)
    with sounddevice.Stream(channels=2, device=[default_in, cable],
                            callback=callback):
        SoundboardApp(local_audio_queue, cable_audio_queue).run()
    local_audio_queue.put(False)
    cable_audio_queue.put(False)
