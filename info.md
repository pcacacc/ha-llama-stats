# llama.cpp Stats

Home Assistant integration for tracking llama.cpp token usage and costs.

- Pairs with a small **Unraid companion plugin** (`unraid/llama_stats.plg`) that parses
  `docker logs` of the llama.cpp container and serves JSON — no metrics daemon needed
- HA polls the plugin endpoint, aggregates monthly statistics, persists everything in `.storage`
- Configurable pricing (USD per million tokens), config flow + options flow

Sensors: monthly input tokens, generated tokens, total tokens, monthly cost, requests.

Full documentation: [README.md](https://github.com/pcacacc/ha-llama-stats/blob/main/README.md)
