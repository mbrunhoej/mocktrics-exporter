import argparse

_parser = argparse.ArgumentParser(description="parser")

_parser.add_argument(
    "-f", "--config-file", help="Configuration file path", type=str, default=None
)
_parser.add_argument(
    "-a", "--api-port", help="Port for the api and UI", type=int, default=8080
)
_parser.add_argument(
    "-m", "--metrics-port", help="Port for metrics", type=int, default=8000
)

# Tolerate unknown args when imported under pytest or other runners
arguments = _parser.parse_known_args()[0]
