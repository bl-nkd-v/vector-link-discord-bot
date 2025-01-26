import os
import re
import asyncio
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
intents.reactions = True  # Need this for reaction handling

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Constants
RICK_BOT_ID = 1081815963990761542
VECTOR_BASE_URL = "https://vec.fun/token"
TRASH_EMOJI = "🗑️"
REACTION_TIMEOUT = 30  # seconds


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


async def remove_reaction_after_delay(message: discord.Message):
    """Remove our trash reaction after the specified timeout."""
    await asyncio.sleep(REACTION_TIMEOUT)
    try:
        # Try to fetch the message to see if it still exists
        channel = message.channel
        await channel.fetch_message(message.id)
        # If message exists, remove our reaction
        await message.remove_reaction(TRASH_EMOJI, bot.user)
    except discord.NotFound:
        # Message was deleted, nothing to do
        return
    except Exception as e:
        print(f"Error removing reaction: {e}")


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """Handle reaction adds to manage message deletion."""
    # Ignore our own reactions
    if payload.user_id == bot.user.id:
        return

    # Only handle trash emoji reactions
    if str(payload.emoji) != TRASH_EMOJI:
        return

    # Get the channel and message
    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return

    try:
        # Get our bot's message that was reacted to
        message = await channel.fetch_message(payload.message_id)
        if not message or message.author != bot.user:
            return

        # Check if this is a reply
        if not message.reference:
            return

        try:
            # Try to get Rick's message
            rick_message = await channel.fetch_message(message.reference.message_id)
            if not rick_message or rick_message.author.id != RICK_BOT_ID:
                await message.delete()
                return
        except discord.NotFound:
            # Rick's message was deleted
            await message.delete()
            return

        try:
            # Try to get the original message Rick replied to
            original_message = await channel.fetch_message(
                rick_message.reference.message_id
            )
            if not original_message:
                await message.delete()
                return

            # Check if the reaction was added by the original message author
            if payload.user_id == original_message.author.id:
                await message.delete()
        except discord.NotFound:
            # Original message was deleted
            await message.delete()

    except discord.NotFound:
        pass  # Our message was already deleted
    except Exception as e:
        print(f"Error handling reaction: {e}")


@bot.event
async def on_message(message: discord.Message):
    # Check environment and guild ID
    environment = os.getenv("ENVIRONMENT", "production")
    development_guild_id = int(os.getenv("DEVELOPMENT_GUILD_ID", "0"))
    if environment == "development" and message.guild.id != development_guild_id:
        return

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

    try:
        # Send reply
        bot_message = await message.reply(view=view)

        try:
            # Add reaction
            await bot_message.add_reaction(TRASH_EMOJI)
            # Start task to remove reaction after delay
            asyncio.create_task(remove_reaction_after_delay(bot_message))
        except discord.Forbidden as e:
            print(f"Bot lacks permission to add reactions: {e}")
        except discord.HTTPException as e:
            print(f"Failed to add reaction: {e}")
        except Exception as e:
            print(f"Unexpected error adding reaction: {e}")

    except Exception as e:
        print(f"Failed to send message or add reaction: {e}")


def main():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN not found in environment variables")
    bot.run(token)


if __name__ == "__main__":
    main()
