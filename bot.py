"""
Discord bot entrypoint for Numora.
Loads configuration, initializes the CrimeBotClient, and runs it.
"""

import logging
import sys

from src.bot.client import CrimeBotClient
from src.utils.config import config, Config


def main() -> None:
    # Basic structured logging to stdout
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
    )

    # Validate required config
    Config.validate()

    token = config.DISCORD_TOKEN
    bot = CrimeBotClient()
    bot.run(token)


if __name__ == "__main__":
    main()

