# Vector Link Discord Bot

A simple Discord bot that listens for messages from the Rick and responds with formatted Vector.fun links. This bot helps bridge the gap by providing Vector.fun links for contract addresses that Rick bot identifies.

## Features

- Automatically detects messages from Rick bot
- Parses contract addresses and chain information
- Generates Vector.fun links with referral code support
- Simple and maintainable codebase

## Setup

1. Clone this repository:

```bash
git clone https://github.com/bl-nkd-v/vector-link-discord-bot.git
cd vector-link-discord-bot
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file:

```bash
cp .env.example .env
```

4. Edit the `.env` file with your:

   - Discord bot token (get it from [Discord Developer Portal](https://discord.com/developers/applications))
   - Vector.fun referral code

5. Run the bot:

```bash
python bot.py
```

## Configuration

The bot uses environment variables for configuration:

- `DISCORD_BOT_CLIENT_ID`: Your Discord bot client ID
- `DISCORD_BOT_CLIENT_SECRET`: Your Discord bot client secret
- `VECTOR_REF_CODE`: Your Vector.fun referral code

You can get your Discord bot client ID and secret from the [Discord Developer Portal](https://discord.com/developers/applications). Your Discord bot must have the `MESSAGE_CONTENT` intent enabled.

## Contributing

Feel free to submit issues and pull requests to improve the bot.

## License

MIT License
