"""Constants for the llama.cpp Stats integration."""

DOMAIN = "llama_stats"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_CONTAINER = "container"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_INPUT_PRICE = "input_price_per_million"
CONF_OUTPUT_PRICE = "output_price_per_million"
CONF_CACHED_PRICE = "cached_input_price_per_million"
CONF_ENERGY_PRICE = "energy_price_per_kwh"
CONF_CURRENCY = "currency"

DEFAULT_PORT = 19877
DEFAULT_CONTAINER = "llama.cpp, strata, gpus"
DEFAULT_SCAN_INTERVAL = 300
DEFAULT_INPUT_PRICE = 0.05
DEFAULT_OUTPUT_PRICE = 0.70
DEFAULT_CACHED_PRICE = 0.03
DEFAULT_ENERGY_PRICE = 0.30
DEFAULT_CURRENCY = "EUR"

DATA_VERSION = 2
