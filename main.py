import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import dotenv
from dotenv import load_dotenv
import os
import logging
import deep_translator
import langcodes
import easy_pil
import pytz

load_dotenv()

intents = discord.Intents.all()

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
logger.addHandler(handler)
logger.addHandler(console_handler)

class MyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix='!b', intents=intents)

    async def setup_hook(self) -> None:
        print('loading cogs...')
        for filename in os.listdir('bot'):
            if filename.endswith('.py') and filename != '__init__.py':
                cog_name = filename[:-3]
                await bot.load_extension(f'bot.{cog_name}')
                print(f'loaded {cog_name}')
        for filename in os.listdir('bot/cogs'):
            if filename.endswith('.py') and filename != '__init__.py':
                cog_name = filename[:-3]
                await bot.load_extension(f'bot.cogs.{cog_name}')
                print(f'loaded {cog_name}')
        print('setup complete')

bot = MyBot()

API_TOKEN = str(os.getenv('API_TOKEN'))

bot.run(API_TOKEN, log_handler=logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w'), log_level=logging.ERROR)