import argparse

_parser = argparse.ArgumentParser(description="parser")

_parser.add_argument("-f", "--config-file", help="Configuration file path", type=str, default=None)
_parser.add_argument("-a", "--api-port", help="Port for the api and UI", type=int, default=8080)
_parser.add_argument("-m", "--metrics-port", help="Port for metrics", type=int, default=8000)

arguments, _ = _parser.parse_known_args()
