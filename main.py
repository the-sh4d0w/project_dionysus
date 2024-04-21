"""Main file for Project Dionysus, a soundboard."""
# some questionable choices were made in the creation of this program
# if something seems illogical it's probably the only way I could get it to work

# TODO:
# - fix text being cut off
# - third text display option?
# - maybe move more stuff into config
# - themes!
# - better option menu

import json
import os
import threading
import queue
import typing

import numpy
import sounddevice
import soundfile
import textual
import textual.app
import textual.containers
import textual.css.query
import textual.screen
import textual.widgets

AUDIO_PATH = "audio/"
CONFIG_PATH = "config.json"
LANG_PATH = "lang/"
DEVICE_NAME = "CABLE Input MME"  # somehow matches correct device
FILE_TYPES = ("mp3", "wav", "ogg")
STANDARD_EMOJI = "🔊"


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


def load_config() -> dict[str, typing.Any]:
    """Load the config from the config file.

    Returns:
        The config as a dict.
    """
    if os.path.isfile(CONFIG_PATH):
        with open(file=CONFIG_PATH, mode="r", encoding="utf-8") as file:
            return json.load(file)
    raise FileNotFoundError("the config does not exist")


def load_language(lang_code: str) -> dict[str, str]:
    """Loads the language file for the provided language.
    Should be a ISO 639-2 code but technically is just the name of a JSON file.

    Arguments:
        - lang_code: language to load.

    Returns:
        The text for the language as a dict.

    Raises:
        NoLanguageError: if no language file can be found.
    """
    if os.path.isfile(f"{LANG_PATH}{lang_code}.json"):
        with open(file=f"{LANG_PATH}{lang_code}.json", mode="r",
                  encoding="utf-8") as file:
            return json.load(file)
    raise FileNotFoundError("the specified language does not exist")


class Text:
    """Class for translatable text."""
    lang_map: dict[str, str] = load_language(load_config()["language"])

    @staticmethod
    def set_language(code: str) -> None:
        """Set the language to use.

        Arguments:
            - code: ISO 639-2 code of the language to load.
        """
        Text.lang_map = load_language(code)

    @staticmethod
    def translatable(key: str, **format_args: typing.Any) -> str:
        """Get translated text if available.

        Arguments:
            - key: key to look for.
            - **format_args: allows optional arguments for formatting.

        Returns:
            The text if it exists, key otherwise.
        """
        return Text.lang_map[key].format_map(format_args) \
            if Text.lang_map.get(key) is not None else key


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

    def __init__(self, file: str) -> None:
        """Initialize the button.

        Arguments:
            - file: name of the sound file.
        """
        self.app: SoundboardApp
        self.file = file
        self.text = os.path.basename(file).split(".")[0]
        self.emoji = STANDARD_EMOJI
        file_name = os.path.basename(file)
        if self.app.config["sounds"].get(file_name):
            if self.app.config["sounds"][file_name].get("text"):
                self.text = self.app.config["sounds"][file_name]["text"]
            textual.log(self.text)
            if self.app.config["sounds"][file_name].get("emoji"):
                self.emoji = self.app.config["sounds"][file_name]["emoji"]
        super().__init__(label=f"{self.emoji} {self.text}",
                         classes="sound-button")
        self.tooltip = self.text

    def press(self) -> None:
        """Do something when button is pressed."""
        try:
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


class LanguageScreen(textual.screen.ModalScreen[str]):
    """Class for the language selection screen."""

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        options: list[tuple[str, str]] = []
        for file in os.listdir(LANG_PATH):
            name: str = os.path.basename(file).split(".")[0]
            options.append((name, name))
        yield textual.widgets.SelectionList[str](*options)

    def on_mount(self) -> None:
        """Change title on mount."""
        self.query_one(textual.widgets.SelectionList).border_title \
            = Text.translatable("language.title")

    @textual.on(textual.widgets.SelectionList.SelectedChanged)
    def choose_language(self) -> None:
        """Choose a language."""
        self.app: SoundboardApp
        lang: str = self.query_one(textual.widgets.SelectionList).selected[0]
        with open(file=CONFIG_PATH, mode="wb") as file:
            self.app.config["language"] = lang
            file.write(json.dumps(self.app.config,
                       ensure_ascii=False).encode())
        self.dismiss(lang)


class SoundboardScreen(textual.screen.Screen):
    """Class for the soundboard screen."""
    TITLE = "Dionysus - Soundboard"
    BINDINGS = [
        ("q", "quit()", Text.translatable("soundboard.footer.quit")),
        ("h", "switch_screen('help')",
         Text.translatable("soundboard.footer.open")),
        ("t", "toggle_text()", Text.translatable("soundboard.footer.toggle")),
        ("r", "reload()", Text.translatable("soundboard.footer.reload")),
        ("l", "change_language()", Text.translatable("soundboard.footer.lang"))
    ]

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        yield textual.widgets.Header(show_clock=True)
        with textual.containers.ScrollableContainer(id="buttons"):
            for entry in os.scandir(AUDIO_PATH):
                if entry.is_file() and entry.path.split(".")[-1].lower() \
                        in FILE_TYPES:
                    yield SoundButton(file=entry.path)
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
            else:
                container.styles.grid_size_columns = 10
                button.label = button.emoji

    def action_reload(self) -> None:
        """Reload the config and sound buttons."""
        self.app: SoundboardApp
        self.app.reload()

    def action_change_language(self) -> None:
        """Change the language."""
        self.app: SoundboardApp
        self.app.push_screen(LanguageScreen(), Text.set_language)


class HelpScreen(textual.screen.Screen):
    """Class for the help screen."""
    TITLE = "Dionysus - Help"
    BINDINGS = [
        ("q", "quit()", Text.translatable("soundboard.footer.quit")),
        ("h", "switch_screen('soundboard')",
         Text.translatable("help.footer.close"))
    ]

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        yield textual.widgets.Header(show_clock=True)
        with textual.containers.Container(id="help"):
            yield FAQ(title=Text.translatable("help.file_question"),
                      text=Text.translatable("help.file_text",
                                             AUDIO_PATH=AUDIO_PATH))
            yield FAQ(title=Text.translatable("help.icon_question"),
                      text=Text.translatable("help.icon_text",
                                             CONFIG_PATH=CONFIG_PATH))
            yield FAQ(title=Text.translatable("help.name_question"),
                      text=Text.translatable("help.name_text",
                                             CONFIG_PATH=CONFIG_PATH))
            yield FAQ(title=Text.translatable("help.sound_question"),
                      text=Text.translatable("help.sound_text"))
            yield FAQ(title=Text.translatable("help.json_question"),
                      text=Text.translatable("help.json_text"))
        yield textual.widgets.Footer()


class SoundboardApp(textual.app.App):
    """Class for the app."""
    CSS_PATH = "main.tcss"
    TITLE = "Dionysus"

    def __init__(self, local_queue: queue.Queue, cable_queue: queue.Queue,
                 lang: str = "eng") -> None:
        """Initialize the soundboard app."""
        super().__init__()
        self.app: SoundboardApp
        self.config: dict[str, typing.Any]
        self.local_queue = local_queue
        self.cable_queue = cable_queue
        self.lang = lang
        # load config for the first time
        self.app.config = load_config()

    def on_mount(self) -> None:
        """Install screens on mount."""
        self.install_screen(SoundboardScreen(), "soundboard")
        self.install_screen(HelpScreen(), "help")
        self.push_screen("soundboard")

    def reload(self) -> None:
        """Reload the config."""
        self.app.config = load_config()
        self.pop_screen()
        self.uninstall_screen("soundboard")
        self.install_screen(SoundboardScreen(), "soundboard")
        self.push_screen("soundboard")
        self.notify(message=Text.translatable("notification.reload.msg"),
                    title=Text.translatable("notification.reload.title"),
                    severity="information")


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
