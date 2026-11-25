"""Constants for the llama.cpp Stats integration."""

DOMAIN = "llama_stats"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_CONTAINER = "container"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_INPUT_PRICE = "input_price_per_million"
CONF_OUTPUT_PRICE = "output_price_per_million"

DEFAULT_PORT = 19877
DEFAULT_CONTAINER = "llama.cpp"
DEFAULT_SCAN_INTERVAL = 300
DEFAULT_INPUT_PRICE = 0.05
DEFAULT_OUTPUT_PRICE = 0.70

DATA_VERSION = 2
