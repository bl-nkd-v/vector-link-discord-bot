import os
import re
from typing import Optional, Tuple
from enum import Enum
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Constants
RICK_BOT_ID = 1081815963990761542
VECTOR_BASE_URL = "https://vec.fun/token"


class ChainInfo(Enum):
    """
    Enum containing chain information.
    Format: CHAIN_NAME = (vector_chain_id, [aliases])
    The CHAIN_NAME should match what appears after the / in Rick's messages (e.g., /SOL)
    vector_chain_id: The identifier used in the vector.fun URL
    """

    SOL = ("SOLANA", ["solana", "sol"])
    ETH = ("ETHEREUM", ["ethereum", "eth"])
    BASE = ("BASE", ["base"])
    RUNES = ("BITCOIN_RUNES", ["bitcoin_runes", "RUNES"])


def parse_contract_info(message: discord.Message) -> Optional[Tuple[str, str]]:
    """
    Parse chain and contract address from Rick bot's message.
    Returns tuple of (chain, contract_address) if found, None otherwise.
    """
    if len(message.embeds) == 0:
        return None

    for embed in message.embeds:
        if not embed.description:
            continue

        # Split description into lines
        lines = embed.description.split("\n")
        if not lines:
            continue

        # Get chain from first line
        first_line = lines[0].lower()
        detected_chain = None
        for chain in ChainInfo:
            # Check if any of the chain's aliases appear in the first line
            if any(alias.lower() in first_line for alias in chain.value[1]):
                detected_chain = chain
                break

        if not detected_chain:
            continue

        # Look for contract address in a code block
        # Reverse the lines since contract usually appears near the bottom
        for line in reversed(lines):
            # For Solana addresses (base58 in code block)
            if detected_chain.name == "SOL":
                matches = re.findall(r"`([1-9A-HJ-NP-Za-km-z]{32,44})`", line)
                for match in matches:
                    # Verify it's a valid base58 address (basic check)
                    if len(match) >= 32 and len(match) <= 44:
                        return detected_chain.value[0].upper(), match
            # For EVM chains (0x addresses)
            else:
                contract_match = re.search(r"`(0x[a-fA-F0-9]{40})`", line)
                if contract_match:
                    return (
                        detected_chain.value[0].upper(),
                        contract_match.group(1).lower(),
                    )

    return None


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.event
async def on_message(message: discord.Message):
    # Only process messages from Rick bot
    if message.author.id != RICK_BOT_ID:
        return

    # Try to parse contract info
    result = parse_contract_info(message)
    if not result:
        return

    chain, contract_address = result
    ref_code = os.getenv("VECTOR_REF_CODE", "")

    # Create vector.fun link
    vector_link = f"{VECTOR_BASE_URL}/{chain}:{contract_address}?ref={ref_code}"

    # Create button view
    view = discord.ui.View()
    button = discord.ui.Button(
        style=discord.ButtonStyle.link,
        label="View on Vector",
        url=vector_link,
        emoji="🔗",
    )
    view.add_item(button)

    # Reply with both link and button for debugging
    await message.reply(f"Vector Link:", view=view)


def main():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN not found in environment variables")
    bot.run(token)


if __name__ == "__main__":
    main()
