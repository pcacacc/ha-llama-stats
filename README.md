# llama.cpp Stats

Home Assistant integration ([HACS](https://hacs.xyz/)) + Unraid companion plugin that tracks llama.cpp token usage and cost over time.

## Architecture

```
llama.cpp container (Unraid)
   └─ llama_stats plugin parses `docker logs` locally (Perl, runs at boot)
         └─ JSON endpoint /metrics?since=<cursor>
               └─ HA integration polls, aggregates monthly, persists in .storage
```

No metrics daemon needed on the NAS beyond the plugin itself: the plugin is stateless
(Home Assistant owns the cursor and all aggregation).

## Unraid plugin

1. Copy `unraid/llama_stats.plg` to `/boot/config/plugins/llama_stats.plg`
2. Reboot Unraid (or run the script) — the server listens on port `19877`
   (`LLAMA_STATS_PORT` / `LLAMA_STATS_CONTAINER` env vars override defaults)
3. Endpoint: `GET /metrics?since=<ISO8601>` → `{"input_tokens":N,"gen_tokens":M,"requests":K,"last_timestamp":"..."}`

It parses the per-request lines `prompt eval time = ... / N tokens` (input) and
`eval time = ... / M tokens` (generated) from `docker logs -t llama.cpp`, ignoring
lines at or before the given `since` timestamp (no double counting).

## Home Assistant installation (HACS)

1. HACS → Integrations → add this repo as custom repository (category **Integration**) → download
2. Restart Home Assistant
3. Settings → Devices & Services → Add Integration → **llama.cpp Stats**
4. Enter host (e.g. `homenas`), port `19877`, container `llama.cpp`, interval and pricing

Replaces any existing `command_line`/template token sensors — remove those and
`llama_tokens.sh` when switching.

## Sensors

| Sensor | Description |
|---|---|
| Input tokens | Current month input tokens |
| Generated tokens | Current month generated tokens |
| Total tokens | Current month total tokens |
| Monthly cost | Cost in USD at the configured pricing |
| Requests | Requests counted this month |

State (cursor + monthly data) is persisted in HA `.storage` and survives restarts.

## Development

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

Tests cover the HA-independent log parser, cost calculation and monthly model.

## License

MIT
