"""Sound button widget."""

import pathlib

import textual.widgets

import soundfile

import main
import utils.config
import utils.translate


class SoundButton(textual.widgets.Button):
    """Class for custom sound button."""

    def __init__(self, file: pathlib.Path) -> None:
        """Initialize the button.

        Arguments:
            - file: path of the sound file.
        """
        self.file = file
        self.text = file.stem
        self.emoji = utils.config.CONFIG.default_emoji
        file_name = file.stem + file.suffix
        if utils.config.SOUNDS.get(file_name):
            if utils.config.SOUNDS[file_name].text:
                self.text = str(utils.config.SOUNDS[file_name].text)
            if utils.config.SOUNDS[file_name].emoji:
                self.emoji = str(utils.config.SOUNDS[file_name].emoji)
        super().__init__(label=f"{self.emoji}\n{self.text}",
                         classes="sound-button")
        self.tooltip = self.text

    def press(self) -> "SoundButton":
        """Do something when button is pressed."""
        try:
            self.app: main.SoundboardApp
            data, samplerate = soundfile.read(file=self.file)
            self.app.local_queue.put((data, samplerate))
            self.app.cable_queue.put((data, samplerate))
        except soundfile.LibsndfileError as exc:
            self.app.notify(message=exc.error_string,
                            title=exc.prefix.removesuffix(": "),
                            severity="error")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.app.notify(message=str(exc), title=utils.translate.Text.translatable(
                "notify.warning"), severity="warning")
        return self
