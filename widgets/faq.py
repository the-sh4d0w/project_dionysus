"""FAQ widget."""

import textual.app
import textual.containers
import textual.widgets


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
