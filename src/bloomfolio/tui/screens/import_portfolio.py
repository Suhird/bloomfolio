"""Import portfolio modal."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from bloomfolio.tui.modals.schema_help import SchemaHelpModal

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from bloomfolio.domain.validation import ValidationResult
    from bloomfolio.tui.app import BloomFolioApp


class ImportPortfolioScreen(ModalScreen[None]):
    """Portfolio import modal overlay."""

    BINDINGS = [
        Binding("q", "quit", "Back", show=True),
        Binding("escape", "escape", "Back", show=True),
        Binding("ctrl+i", "do_import", "Import", show=False),
        Binding("ctrl+v", "do_validate", "Validate", show=False),
        Binding("ctrl+h", "schema_help", "Schema", show=False),
    ]

    DEFAULT_CSS = """
    ImportPortfolioScreen {
        align: center middle;
    }
    ImportPortfolioScreen > Container {
        width: 90;
        height: auto;
        max-height: 90%;
        padding: 2 4;
        border: thick $primary;
        background: $surface;
    }
    ImportPortfolioScreen .path-input {
        margin: 1 0;
    }
    ImportPortfolioScreen .status {
        margin: 1 0;
        height: auto;
    }
    ImportPortfolioScreen .diagnostics {
        margin: 1 0;
        height: auto;
        color: $error;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Import Portfolio CSV", classes="title")
            yield Static("Enter the path to your Wealthsimple CSV export:")

            yield Input(
                placeholder="/path/to/portfolio.csv",
                classes="path-input",
                id="path-input",
            )

            with Horizontal():
                yield Button("Import (Ctrl+I)", variant="primary", id="import-btn")
                yield Button("Validate (Ctrl+V)", variant="default", id="validate-btn")
                yield Button("Schema Help (Ctrl+H)", variant="default", id="schema-help-btn")
                yield Button("Back (q)", variant="error", id="back-btn")

            yield Static("Status: Ready", classes="status", id="status")
            yield Static("", classes="diagnostics", id="diagnostics")

            with VerticalScroll(id="results"):
                yield Static("Import results will appear here.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app: BloomFolioApp = self.app  # type: ignore[assignment]

        if event.button.id == "import-btn":
            self._do_import()
        elif event.button.id == "validate-btn":
            self._do_validate()
        elif event.button.id == "schema-help-btn":
            app.push_screen(SchemaHelpModal())
        elif event.button.id == "back-btn":
            self.dismiss()

    def action_do_import(self) -> None:
        """Keyboard shortcut for Import."""
        self._do_import()

    def action_do_validate(self) -> None:
        """Keyboard shortcut for Validate."""
        self._do_validate()

    def action_schema_help(self) -> None:
        """Keyboard shortcut for Schema Help."""
        self.app.push_screen(SchemaHelpModal())

    def action_quit(self) -> None:
        """Close modal."""
        self.dismiss()

    def action_escape(self) -> None:
        """Close modal."""
        self.dismiss()

    def _do_import(self) -> None:
        """Import the CSV file."""
        path_input = self.query_one("#path-input", Input)
        path = path_input.value.strip()

        if not path:
            self._update_status("Please enter a file path", error=True)
            return

        import asyncio

        asyncio.create_task(self._import_async(path))

    def _do_validate(self) -> None:
        """Validate the CSV file without importing."""
        path_input = self.query_one("#path-input", Input)
        path = path_input.value.strip()

        if not path:
            self._update_status("Please enter a file path", error=True)
            return

        import asyncio

        asyncio.create_task(self._validate_async(path))

    async def _import_async(self, path: str) -> None:
        """Async import implementation."""
        app: BloomFolioApp = self.app  # type: ignore[assignment]
        self._update_status(f"Importing {path}...")

        try:
            from bloomfolio.portfolio.csv_importer import import_csv

            portfolio = await import_csv(path)
            app.current_portfolio = portfolio
            self._update_status(
                f"Imported {len(portfolio.holdings)} holdings from {portfolio.source_file_name}",
                error=False,
            )
            self.dismiss()
        except Exception as e:
            self._update_status(f"Import failed: {e}", error=True)

    async def _validate_async(self, path: str) -> None:
        """Async validation implementation."""
        self._update_status(f"Validating {path}...")

        try:
            from bloomfolio.portfolio.validator import validate_csv_file

            result = await validate_csv_file(path)
            if result.valid:
                self._update_status(
                    f"Valid! {result.row_count} rows, {result.column_count} columns.",
                    error=False,
                )
            else:
                self._update_status(
                    f"Invalid: {len([e for e in result.errors if e.severity == 'ERROR'])} errors, "
                    f"{len(result.warnings)} warnings",
                    error=True,
                )
                self._show_diagnostics(result)
        except Exception as e:
            self._update_status(f"Validation failed: {e}", error=True)

    def _update_status(self, message: str, error: bool = False) -> None:
        status = self.query_one("#status", Static)
        status.update(message)
        status.styles.color = "red" if error else "green"

    def _show_diagnostics(self, result: ValidationResult) -> None:
        diag = self.query_one("#diagnostics", Static)
        lines = []
        for item in result.get_diagnostics()[:20]:
            lines.append(
                f"{item.severity} row={item.row_number} field={item.field}: {item.message}"
            )
        diag.update("\n".join(lines) if lines else "No diagnostics")
