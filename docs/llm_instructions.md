# LLM Model Selection Guide

BloomFolio runs multi-agent analysis through a local Ollama server. The model you choose has a dramatic effect on both analysis quality and runtime.

## Quick Recommendations

| Use Case | Recommended Model | Est. Time per Call | 72 Calls Total |
|----------|-------------------|-------------------|----------------|
| Fast testing / development | `gemma4:4b` | 10–20 sec | 10–20 min |
| Balanced speed + quality | `gemma4:9b` | 30–60 sec | 30–60 min |
| Best quality (slower) | `gemma4:26b` | 2–3 min | 2.5–4 hours |
| Strong JSON instruction follower | `qwen2.5:7b` | 20–40 sec | 20–40 min |
| Reliable structured output | `llama3.1:8b` | 20–40 sec | 20–40 min |

## Trade-Offs

### Larger models (26B+)
- **Pros:** Better reasoning, more coherent analysis, fewer JSON validation failures
- **Cons:** Very slow (2–3 min per stage), long total runtime, heavy VRAM usage

### Smaller models (4B–9B)
- **Pros:** 10–50× faster, low VRAM footprint, great for iterating
- **Cons:** May produce malformed JSON more often (BloomFolio retries once), less nuanced analysis

## How to Switch Models

### 1. Pull the model
```bash
ollama pull gemma4:9b
```

### 2. Update your `.env` file
```bash
# ~/.local/share/bloomfolio/.env or project root .env
BLOOMFOLIO_OLLAMA_QUICK_MODEL=gemma4:9b
BLOOMFOLIO_OLLAMA_DEEP_MODEL=gemma4:9b
```

### 3. Verify it's loaded
```bash
ollama ps
# Should show gemma4:9b
```

### 4. Restart BloomFolio
```bash
uv run bloomfolio tui
```

## AMD GPU Users (ROCm)

If you have a newer AMD GPU (e.g., Strix Halo / gfx1151) that Ollama doesn't recognize natively, force the GFX version:

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/rocm-override.conf << 'EOF'
[Service]
Environment="HSA_OVERRIDE_GFX_VERSION=11.5.1"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Verify GPU is being used:
```bash
watch -n 1 rocm-smi
# GPU% should jump during inference, not CPU
```

## Monitoring Ollama

Watch live server logs:
```bash
journalctl -u ollama -f
```

Check currently loaded model:
```bash
ollama ps
```

## Why JSON Validation Errors Happen

The fallback analysis graph sends 9 prompts per ticker, each requesting strict JSON matching a Pydantic schema. Models sometimes:
- Add extra text after the JSON block
- Miss required fields
- Use wrong types (string instead of number)

BloomFolio handles this by:
1. Attempting one automatic repair prompt
2. Logging the failure and continuing with partial results
3. Writing all failures to `~/.local/share/bloomfolio/logs/bloomfolio.log`

## Changing Log Level

If you want to see more (or less) detail:
```bash
# .env
BLOOMFOLIO_LOG_LEVEL=DEBUG   # verbose
BLOOMFOLIO_LOG_LEVEL=WARNING # quieter
```

Logs are written to `~/.local/share/bloomfolio/logs/bloomfolio.log` so they don't pollute the TUI.
