"""Entrypoint for the CluesBySam → Google Sheets Discord bot."""

from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )
    from bot import run_bot

    run_bot()


if __name__ == "__main__":
    main()
