"""Exit screen."""

import textual.app
import textual.containers
import textual.screen
import textual.widgets

# TODO: translate text


class ExitScreen(textual.screen.ModalScreen[str]):
    """Exit modal screen."""

    def compose(self) -> textual.app.ComposeResult:
        """Compose the ui."""
        with textual.containers.Grid(id="dialog"):
            yield textual.widgets.Label(
                "You need to restart to apply changes.\nDo you want to exit?",
                id="question")
            yield textual.widgets.Button("Quit", id="quit")
            yield textual.widgets.Button("Cancel", id="cancel")

    @textual.on(textual.widgets.Button.Pressed, "#quit")
    def pressed_quit(self, event: textual.widgets.Button.Pressed) -> None:
        """Handle button pressed event for quit."""
        event.stop()
        self.app.exit()

    @textual.on(textual.widgets.Button.Pressed, "#cancel")
    def pressed_cancel(self, event: textual.widgets.Button.Pressed) -> None:
        """Handle button pressed event for cancel."""
        event.stop()
        self.app.pop_screen()
