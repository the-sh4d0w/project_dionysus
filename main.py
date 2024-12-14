"""Main file for Project Dionysus, a soundboard."""

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
import textual.design
import textual.reactive
import textual.screen
import textual.signal
import textual.widgets

import screens.soundboard
import utils.config

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
    ENABLE_COMMAND_PALETTE = False
    TITLE = "Dionysus"
    CSS_PATH = "./config/style.tcss"

    def __init__(self, local_queue: queue.Queue, cable_queue: queue.Queue) -> None:
        """Initialize the soundboard app."""
        super().__init__()
        self.theme = utils.config.CONFIG.theme
        self.local_queue: queue.Queue = local_queue
        self.cable_queue: queue.Queue = cable_queue

    def on_mount(self) -> None:
        """Do stuff on mount."""
        self.push_screen(screens.soundboard.SoundboardScreen())


if __name__ == "__main__":
    default_in, default_out, cable = get_devices()
    local_audio_queue = queue.Queue()
    cable_audio_queue = queue.Queue()
    try:
        threading.Thread(target=audio_thread,
                         args=(local_audio_queue, default_out)).start()
        threading.Thread(target=audio_thread,
                         args=(cable_audio_queue, cable)).start()
        # should always be 2 channels (probably)
        with sounddevice.Stream(channels=1, device=[default_in, cable],
                                callback=callback):
            SoundboardApp(local_audio_queue, cable_audio_queue).run()
    except Exception as excp:  # pylint:disable=broad-exception-caught
        print(excp.with_traceback(None))
    finally:
        local_audio_queue.put(False)
        cable_audio_queue.put(False)
