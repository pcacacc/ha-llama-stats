# llama.cpp Stats

Home Assistant integration for tracking llama.cpp token usage and costs.

- Polls a llama.cpp metrics endpoint (JSON: `input_tokens`, `gen_tokens`, `total_tokens`)
- Aggregates monthly statistics and persists them across restarts
- Configurable pricing (USD per million tokens)
- Config flow with UI options (interval + pricing)

Sensors: monthly input tokens, generated tokens, total tokens, monthly cost, snapshot count.

Full documentation: [README.md](https://github.com/pacacc/ha-llama-stats/blob/main/README.md)
