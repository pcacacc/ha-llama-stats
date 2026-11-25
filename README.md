# llama.cpp Stats

Home Assistant integration ([HACS](https://hacs.xyz/)) that tracks llama.cpp token usage and cost over time.

## Features

- Polls a llama.cpp metrics endpoint that returns JSON:
  ```json
  {"input_tokens": 1750531, "gen_tokens": 11614683, "total_tokens": 13365214}
  ```
- Monthly statistics, persisted to `llama_stats_monthly.json` in the Home Assistant config directory (survives llama.cpp restarts)
- Cost calculation with configurable pricing (USD per million tokens)
- Full config flow: set endpoint, poll interval and pricing from the UI, no YAML needed
- Snapshot history per month

## Installation (HACS)

1. Open HACS → Integrations → search for **llama.cpp Stats** → download
2. Restart Home Assistant
3. Settings → Devices & Services → Add Integration → **llama.cpp Stats**
4. Enter the metrics endpoint URL (e.g. `http://192.168.0.207:19876/metrics`)

Without HACS: copy `custom_components/llama_stats/` to `<config>/custom_components/` and restart.

## Sensors

| Sensor | Description |
|---|---|
| Input tokens | Current month input tokens |
| Generated tokens | Current month generated tokens |
| Total tokens | Current month total tokens |
| Monthly cost | Cost in USD at the configured pricing |
| Snapshots | Number of snapshots recorded this month |

## Development

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

Tests cover the HA-independent store and cost calculation.

## License

MIT
