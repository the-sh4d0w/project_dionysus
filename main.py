"""Main file for Project Dionysus, a soundboard."""
# some questionable choices were made in the creation of this program
# if something seems illogical it's probably the only way I could get it to work
# I know, that nobody else is going to read this, this comment is for my future self

import json
import os
import threading
import queue

import numpy
import sounddevice
import soundfile
import textual.app
import textual.containers
import textual.screen
import textual.widgets

AUDIO_PATH = "audio/"
CONFIG_PATH = "config.json"
DEVICE_NAME = "CABLE Input MME"  # somehow matches correct device
FILE_TYPES = ("mp3", "wav", "ogg")
STANDARD_EMOJI = "🔊"


FILE_TEXT = f"""
Put your audio files into the '{AUDIO_PATH}' folder.
The following file formats are supported: mp3, ogg, wav.
"""
ICON_TEXT = f"""
Add an entry in '{CONFIG_PATH}'.
If your file is named 'example.mp3' the entry would look like this:
\"example.mp3\": {{\"emoji\": \"💎\"}}
"""
NAME_TEXT = f"""
Add an entry in '{CONFIG_PATH}'.
If your file is named 'example.mp3' the entry would look like this:
\"example.mp3\": {{\"name\": \"Example name\"}}
"""
SOUND_TEXT = """
Just click on the buttons.
"""
JSON_TEXT = """
https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/JSON
"""


class NoCableError(Exception):
    """Error to raise if VB-Audio Virtual Cable is not correctly installed."""


def get_devices() -> tuple[int, int, int]:
    """Get all devices.

    Returns:
        The default input, default output and CABLE Input device ids.
    """
    try:
        return *sounddevice.default.device, sounddevice.query_devices(DEVICE_NAME)["index"]
    except ValueError as exc:
        raise NoCableError(
            "You don't have VB-Audio Virtual Cable installed.") from exc


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

    def __init__(self, file: str) -> None:
        """Initialize the button.

        Arguments:
            - file: name of the sound file.
        """
        self.file = file
        self.text = os.path.basename(file).split(".")[0]
        self.emoji = STANDARD_EMOJI
        file = os.path.basename(file)
        if self.app.config.get(file):
            if self.app.config[file].get("text"):
                self.text = self.app.config[file]["text"]
            if self.app.config[file].get("emoji"):
                self.emoji = self.app.config[file]["emoji"]
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


class SoundboardScreen(textual.screen.Screen):
    """Class for the soundboard screen."""
    TITLE = "Dionysus- Soundboard"
    BINDINGS = [
        ("h", "switch_screen('help')", "Open help"),
        ("t", "toggle_text()", "Toggle text"),
        ("r", "reload()", "Reload config and audio")
    ]

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        yield textual.widgets.Header(show_clock=True)
        with textual.containers.ScrollableContainer(id="buttons"):
            for entry in os.scandir(AUDIO_PATH):
                if entry.is_file() and entry.path.split(".")[-1].lower() in FILE_TYPES:
                    yield SoundButton(file=entry.path)
        yield textual.widgets.Footer()

    def action_toggle_text(self) -> None:
        """Toggle the text."""
        button: SoundButton
        container: textual.containers.ScrollableContainer = self.query_one(
            "#buttons")
        for button in self.query(".sound-button"):  # pylint: disable=not-an-iterable
            if str(button.label) == button.emoji:
                container.styles.grid_size_columns = 5
                button.label = f"{button.emoji} {button.text}"
            else:
                container.styles.grid_size_columns = 10
                button.label = button.emoji

    def action_reload(self) -> None:
        """Reload the config and sound buttons."""
        self.app.reload()


class HelpScreen(textual.screen.Screen):
    """Class for the help screen."""
    TITLE = "Dionysus - Help"
    BINDINGS = [
        ("h", "switch_screen('soundboard')", "Close help")
    ]

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        yield textual.widgets.Header(show_clock=True)
        with textual.containers.Container(id="help"):
            yield FAQ(title="How do I add audio files?", text=FILE_TEXT)
            yield FAQ(title="How do I change the icons?", text=ICON_TEXT)
            yield FAQ(title="How do I change the names?", text=NAME_TEXT)
            yield FAQ(title="How do I play sounds?", text=SOUND_TEXT)
            yield FAQ(title="I don't understand the config file.", text=JSON_TEXT)
        yield textual.widgets.Footer()


class SoundboardApp(textual.app.App):
    """Class for the app."""
    CSS_PATH = "main.tcss"
    TITLE = "Dionysus"

    def __init__(self, local_queue: queue.Queue, cable_queue: queue.Queue) -> None:
        """Initialize the soundboard app."""
        super().__init__()
        self.config: dict[str, dict] = {}
        self.local_queue = local_queue
        self.cable_queue = cable_queue
        # load config for the first time
        if os.path.isfile(CONFIG_PATH):
            with open(file=CONFIG_PATH, mode="r", encoding="utf-8") as file:
                self.app.config = json.load(file)

    def on_mount(self) -> None:
        """Install screens on mount."""
        self.install_screen(SoundboardScreen(), "soundboard")
        self.install_screen(HelpScreen(), "help")
        self.push_screen("soundboard")

    def reload(self) -> None:
        """Reload the config."""
        if os.path.isfile(CONFIG_PATH):
            with open(file=CONFIG_PATH, mode="r", encoding="utf-8") as file:
                self.app.config = json.load(file)
        self.pop_screen()
        self.uninstall_screen("soundboard")
        self.install_screen(SoundboardScreen(), "soundboard")
        self.push_screen("soundboard")
        self.notify(message="Reloaded config and all sound effects",
                    title="Successfully reloaded", severity="information")


if __name__ == "__main__":
    default_in, default_out, cable = get_devices()
    local_audio_queue = queue.Queue()
    cable_audio_queue = queue.Queue()
    threading.Thread(target=audio_thread,
                     args=(local_audio_queue, default_out)).start()
    threading.Thread(target=audio_thread,
                     args=(cable_audio_queue, cable)).start()
    # should alway be 2 channels (probably)
    with sounddevice.Stream(channels=2, device=[default_in, cable], callback=callback):
        SoundboardApp(local_audio_queue, cable_audio_queue).run()
    local_audio_queue.put(False)
    cable_audio_queue.put(False)
