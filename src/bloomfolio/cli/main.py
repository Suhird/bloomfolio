"""CLI entry point using Typer."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Annotated

import typer

from bloomfolio.config.settings import get_settings
from bloomfolio.observability.logging import configure_logging, get_logger

app = typer.Typer(name="bloomfolio", help="Terminal Portfolio Intelligence")
logger = get_logger(__name__)


def _version_callback(value: bool) -> None:
    if value:
        from bloomfolio import __version__

        typer.echo(f"BloomFolio {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-v", callback=_version_callback),
) -> None:
    """BloomFolio CLI."""
    configure_logging()


@app.command()
def tui() -> None:
    """Launch the terminal UI."""
    from bloomfolio.tui.app import BloomFolioApp

    bloomfolio_app = BloomFolioApp()
    bloomfolio_app.run()


@app.command()
def validate(
    path: Annotated[Path, typer.Argument(help="Path to portfolio CSV file")],
) -> None:
    """Validate a portfolio CSV file."""
    from bloomfolio.portfolio.validator import validate_csv_file

    async def _run() -> None:
        result = await validate_csv_file(str(path))
        if result.valid:
            typer.echo(f"Valid: {result.row_count} rows, {result.column_count} columns")
        else:
            typer.echo(f"Invalid: {len([e for e in result.errors if e.severity == 'ERROR'])} errors")
            for item in result.get_diagnostics()[:20]:
                typer.echo(f"  {item.severity} row={item.row_number} field={item.field}: {item.message}")
            raise typer.Exit(1)

    asyncio.run(_run())


@app.command()
def analyze(
    path: Annotated[Path, typer.Argument(help="Path to portfolio CSV file")],
    tickers: Annotated[str | None, typer.Option("--tickers", "-t", help="Comma-separated tickers")] = None,
) -> None:
    """Analyze a portfolio CSV file."""
    typer.echo("Analysis command not yet implemented.")


@app.command()
def export(
    portfolio_id: Annotated[str, typer.Option("--portfolio-id", help="Portfolio ID")],
    fmt: Annotated[str, typer.Option("--format", "-f", help="Export format")] = "markdown",
    output: Annotated[Path, typer.Option("--output", "-o", help="Output path")] = Path("report.md"),
) -> None:
    """Export a portfolio report."""
    typer.echo("Export command not yet implemented.")


@app.command()
def doctor() -> None:
    """Check system health and dependencies."""
    import importlib.util

    typer.echo("BloomFolio Doctor")
    typer.echo("-" * 40)

    # Python version
    py_version = sys.version_info
    ok = py_version >= (3, 12)
    typer.echo(f"{'[OK]' if ok else '[FAIL]'} Python {py_version.major}.{py_version.minor}.{py_version.micro} (need >= 3.12)")

    # uv check
    try:
        import subprocess
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=False)
        ok = result.returncode == 0
        typer.echo(f"{'[OK]' if ok else '[WARN]'} uv {'found' if ok else 'not found'}")
    except FileNotFoundError:
        typer.echo("[WARN] uv not found in PATH")

    # Textual
    try:
        import textual
        typer.echo(f"[OK] Textual {textual.__version__}")
    except ImportError:
        typer.echo("[FAIL] Textual not installed")

    # Ollama
    settings = get_settings()
    import httpx
    try:
        r = httpx.get(settings.ollama_base_url.replace("/v1", "/api/tags"), timeout=5.0)
        if r.status_code == 200:
            models = [m.get("name", "") for m in r.json().get("models", [])]
            quick_ok = settings.ollama_quick_model in models
            deep_ok = settings.ollama_deep_model in models
            typer.echo(f"[OK] Ollama running at {settings.ollama_base_url}")
            typer.echo(f"{'[OK]' if quick_ok else '[WARN]'} Quick model: {settings.ollama_quick_model}")
            typer.echo(f"{'[OK]' if deep_ok else '[WARN]'} Deep model: {settings.ollama_deep_model}")
        else:
            typer.echo(f"[FAIL] Ollama returned {r.status_code}")
    except Exception as e:
        typer.echo(f"[FAIL] Ollama unreachable: {e}")
        typer.echo("  Fix: ollama serve")

    # TradingAgents
    spec = importlib.util.find_spec("tradingagents")
    if spec:
        typer.echo("[OK] TradingAgents package found")
    else:
        typer.echo("[INFO] TradingAgents not installed (fallback graph will be used)")

    # SQLite path
    db_dir = settings.db_path.parent
    try:
        db_dir.mkdir(parents=True, exist_ok=True)
        typer.echo(f"[OK] Data directory writable: {db_dir}")
    except Exception as e:
        typer.echo(f"[FAIL] Data directory not writable: {e}")

    typer.echo("-" * 40)
    typer.echo("Run 'bloomfolio' to start the TUI.")


if __name__ == "__main__":
    app()
