# BloomFolio

**Terminal Portfolio Intelligence**

A Bloomberg-terminal-inspired Python TUI that imports a Wealthsimple portfolio CSV, validates holdings schema, runs TradingAgents-style multi-agent analysis per ticker using a locally hosted Gemma 4 model via Ollama, and presents portfolio-aware market intelligence in an async, keyboard-driven interface.

This project is very much inspired by [TradingAgents](https://github.com/tauricresearch/tradingagents) — it is not a direct fork, but the multi-agent analysis approach draws heavily from its design.

> **Disclaimer:** This application is for research and educational analysis only. It does not provide financial, investment, tax, or trading advice. AI-generated outputs may be incomplete, stale, or wrong. Always verify data independently and consult a qualified professional before making financial decisions.

## Quickstart

```bash
git clone <repo>
cd bloomfolio

uv sync

ollama pull gemma4
ollama serve

cp .env.example .env

uv run bloomfolio doctor
uv run bloomfolio tui
```

## Features

- **Portfolio Import**: Import and validate Wealthsimple CSV exports
- **Multi-Agent Analysis**: Fundamental, Technical, News, Sentiment, Bull/Bear, Trader, Risk, Portfolio Manager
- **Local-First**: Runs entirely on your machine with Ollama
- **Responsive TUI**: Textual-based terminal UI with vim-style navigation
- **Structured Output**: All AI outputs are JSON-schema validated
- **Audit Trail**: Every action is logged for traceability
- **Export**: Markdown and JSON reports

## CSV Schema

See [docs/csv_schema.md](docs/csv_schema.md) for the full accepted schema.

## Architecture

See [docs/architecture.md](docs/architecture.md) for architecture details.

## License

MIT
