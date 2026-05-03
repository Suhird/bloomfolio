# Architecture

## Overview

BloomFolio is a local-first terminal application for portfolio analysis using multi-agent LLM workflows.

## Components

### TUI (`bloomfolio/tui/`)

Textual-based terminal UI with Bloomberg-inspired theme.

- **Screens**: Startup, Import, Portfolio Overview, Agent Monitor, Export
- **Widgets**: Footer, tables, progress bars, log panels
- **Modals**: Help, Schema Help

### Portfolio (`bloomfolio/portfolio/`)

CSV import and validation pipeline.

- **csv_importer.py**: Async CSV parsing into domain models
- **validator.py**: Schema validation with detailed diagnostics
- **normalizer.py**: Column alias normalization
- **aggregation.py**: Portfolio aggregation utilities

### Agents (`bloomfolio/agents/`)

Multi-agent analysis orchestration.

- **tradingagents_gateway.py**: Adapter for upstream TradingAgents
- **fallback_graph.py**: Internal multi-agent workflow when TradingAgents unavailable
- **runner.py**: Portfolio-wide analysis orchestration
- **prompts.py**: Prompt builders for each agent stage
- **schemas.py**: Pydantic schemas for structured agent outputs

### LLM (`bloomfolio/llm/`)

LLM gateway with structured output validation.

- **client.py**: Universal LLM client (Ollama/OpenRouter)
- **structured_output.py**: JSON parsing and schema validation

### Storage (`bloomfolio/storage/`)

SQLite persistence with audit trail.

- **db.py**: Async SQLite connection management
- **audit.py**: Audit event logging
- **cache.py**: TTL-based caching
- **export.py**: Markdown and JSON export

### Domain (`bloomfolio/domain/`)

Core domain models.

- **portfolio.py**: Holding and Portfolio models
- **reports.py**: AnalystReport, TradingDecision, TickerAnalysisResult
- **money.py**: Decimal-based money value object
- **enums.py**: AssetType, AnalysisStage, Rating, etc.
- **exceptions.py**: Typed exceptions

## Data Flow

```
User CSV -> Validator -> Importer -> Portfolio Model -> Storage
                                          |
                                          v
                                    Analysis Runner
                                          |
                    +---------------------+---------------------+
                    |                                           |
            TradingAgents Gateway                      Fallback Graph
                    |                                           |
                    +---------------------+---------------------+
                                          |
                                    LLM Gateway
                                          |
                              Ollama / OpenRouter
```

## Async Architecture

- Textual app runs in async mode
- Slow work (LLM calls, CSV parsing) runs in threads via `asyncio.to_thread` or `run_in_executor`
- SQLite uses `aiosqlite`
- HTTP uses `httpx.AsyncClient`
- Concurrency controlled by semaphores
