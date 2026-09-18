"""Allows `python -m aifootprint_cli` as an alternative to the
installed `aifootprint` console script.
"""

from .cli import run

if __name__ == "__main__":
    run()
