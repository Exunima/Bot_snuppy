import discord
from discord.ext import commands
from config import DISCORD_BOT_TOKEN
from music import player

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)
player.setup(bot)


@bot.event
async def on_ready():
    print(f"Бот запущен: {bot.user.name}")

bot.run(DISCORD_BOT_TOKEN)
