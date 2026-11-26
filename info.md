# llama.cpp Stats

Home Assistant integration for tracking llama.cpp token usage and costs.

- Pairs with a small **Unraid companion plugin** (`unraid/llama_stats.plg`) that parses
  `docker logs` of the llama.cpp container and serves JSON — no metrics daemon needed
- HA polls the plugin endpoint, aggregates monthly statistics, reads AMD GPU power from Unraid hwmon, and persists everything in `.storage`
- Configurable token pricing, cached-token pricing, energy price per kWh, currency, config flow + options flow
- Cached/reused input tokens are parsed when the source reports them, e.g. Strata `prompt N tokens = X reused + Y read`

Sensors: input tokens, cached input tokens, generated tokens, total tokens, token cost, energy, energy cost, net cost, requests, total GPU power, and per-GPU power sensors for discovered AMD GPUs.

Full documentation: [README.md](https://github.com/pcacacc/ha-llama-stats/blob/main/README.md)
