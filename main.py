"""Main file for Project Dionysus, a soundboard."""

import threading
import queue

import numpy
import rich
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
import utils.translate

DEVICE_NAME = "CABLE Input MME"  # somehow matches correct device
FILE_TYPES = (".mp3", ".wav", ".ogg")


def callback(indata: numpy.ndarray, outdata: numpy.ndarray, frames, time, status) \
        -> None:  # pylint: disable=unused-argument
    """Callback function."""
    outdata[:] = indata


def audio_thread(audio_queue: queue.Queue) -> None:
    """Function for audio threads. Waits for audio then plays on device.

    Arguments:
        - audio_queue: the queue to get the audio from.
    """
    while (data := audio_queue.get()):
        audio_data, samplerate, device = data
        sounddevice.play(data=audio_data, samplerate=samplerate,
                         device=device, blocking=True)


class SoundboardApp(textual.app.App):
    """Class for the app."""
    ENABLE_COMMAND_PALETTE = False
    TITLE = "Dionysus"
    CSS_PATH = "./config/style.tcss"

    def __init__(self, local_audio_queue: queue.Queue, virtual_audio_queue: queue.Queue) -> None:
        """Initialize the soundboard app."""
        super().__init__()
        self.theme = utils.config.CONFIG.theme
        self.local_audio_queue: queue.Queue = local_audio_queue
        self.virtual_audio_queue: queue.Queue = virtual_audio_queue

    def on_mount(self) -> None:
        """Do stuff on mount."""
        self.push_screen(screens.soundboard.SoundboardScreen())


if __name__ == "__main__":
    # need to play two audios at the same time
    local_queue = queue.Queue()
    virtual_queue = queue.Queue()
    try:
        threading.Thread(target=audio_thread, args=(local_queue,),
                         daemon=True).start()
        threading.Thread(target=audio_thread, args=(virtual_queue,),
                         daemon=True).start()
        with sounddevice.Stream(device=[utils.config.CONFIG.input_device,
                                        utils.config.CONFIG.virtual_output_device],
                                callback=callback):
            SoundboardApp(local_queue, virtual_queue).run()
    except Exception as excp:  # pylint:disable=broad-exception-caught
        print(excp)
        rich.print(
            f"[red]{utils.translate.Text.translatable('error.audio_devices')}")
        utils.config.CONFIG.store_reset()
    finally:
        local_queue.put(False)
        virtual_queue.put(False)
