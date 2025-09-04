import argparse

_parser = argparse.ArgumentParser(description="parser")

_parser.add_argument(
    "-f", "--config-file", help="Configuration file path", type=str, default=None
)

arguments = _parser.parse_args()
