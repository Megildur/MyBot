import discord
from discord.ext import commands
import logging
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

class ServerJoinLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("bot_server_joins")
        self.logger.setLevel(logging.INFO)
        self.handler = logging.FileHandler(filename="bot_server_joins.log", encoding="utf-8", mode="a")
        self.handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        self.logger.addHandler(self.handler)
        self.session = aiohttp.ClientSession()  # Reuse session
        print('API Request Logger cog is loaded')
            
    async def send_webhook_message(self, webhook_url, message):
        data = {"content": message}
        try:
            async with self.session.post(webhook_url, json=data) as response:
                if response.status != 200:
                    self.logger.error(f"Error sending webhook message: {response.status} {response.reason}")
                else:
                    self.logger.info("Webhook message sent successfully")
        except Exception as e:
            self.logger.error(f"Exception occurred: {str(e)}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.logger.info(f"Guild Join: {guild.name} ({guild.id})")
        webhook_url = str(os.getenv('WEBHOOK_URL'))
        message = f"Joined server: {guild.name} ({guild.id})"
        await self.send_webhook_message(webhook_url, message)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.logger.info(f"Guild Remove: {guild.name} ({guild.id})")
        webhook_url = str(os.getenv('WEBHOOK_URL'))
        message = f"Left server: {guild.name} ({guild.id})"
        await self.send_webhook_message(webhook_url, message)

    async def cog_unload(self):  # Cleanup for session
        await self.session.close()

async def setup(bot):
    await bot.add_cog(ServerJoinLogger(bot))