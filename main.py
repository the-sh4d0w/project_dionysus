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

import pathlib
import threading
import queue
import typing

import numpy
import sounddevice
import textual
import textual.app
import textual.color
import textual.containers
import textual.css.query
import textual.css.stylesheet
import textual.screen
import textual.widgets

import screens.config
import screens.exit
import screens.help
import screens.soundboard
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
        self.install_screen(
            screens.soundboard.SoundboardScreen(), "soundboard")
        self.install_screen(screens.help.HelpScreen(), "help")
        self.install_screen(screens.config.ConfigScreen(), "config")
        self.push_screen("soundboard")

    def reload(self) -> None:
        """Reload the config."""
        # FIXME: reload all screens; maybe automatically?
        # I don't need to reinstall, do I; just pop and push, right?
        self.pop_screen()
        self.uninstall_screen("soundboard")
        self.install_screen(screens.soundboard.SoundboardScreen(),
                            "soundboard")
        self.uninstall_screen("help")
        self.install_screen(screens.help.HelpScreen(), "help")
        self.uninstall_screen("config")
        self.install_screen(screens.config.ConfigScreen(), "config")
        self.push_screen("soundboard")
        self.notify(message=util.Text.translatable("notification.reload.msg"),
                    title=util.Text.translatable("notification.reload.title"),
                    severity="information")

    def update_theme(self) -> None:
        """Update the theme."""
        # TODO/FIXME: replace update_theme with get_css_variables
        # IT LITERALLY MENTIONS OVERRIDING get_css_variables TO INTRODUCE \
        # NEW VARIABLES

    async def action_quit(self) -> None:
        """Quit the app and save the config."""
        # FIXME: writes theme and color to config, shouldn't
        # util.Config.save()
        await super().action_quit()
        # can't I just exit?


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
