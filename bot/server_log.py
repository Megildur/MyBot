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
        self.session = aiohttp.ClientSession()
            
    async def send_webhook_message(self, webhook_url, embed: discord.Embed):
        data = {
            "embeds": [embed.to_dict()]
        }
        try:
            async with self.session.post(webhook_url, json=data) as response:
                if response.status in {200, 204}:
                    self.logger.info("Webhook message sent successfully")
        except Exception as e:
            self.logger.error(f"Exception occurred: {str(e)}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.logger.info(f"Guild Join: {guild.name} ({guild.id})\nOwner: {guild.owner.name} ({guild.owner.id})")
        webhook_url = str(os.getenv('BOT_WEBHOOK_URL'))
        embed = discord.Embed(description=f"Joined Server: **{guild.name}** \n({guild.id})", color=discord.Color.green(), timestamp=discord.utils.utcnow())
        embed.add_field(name="Owner", value=f"{guild.owner.name}", inline=False)
        embed.add_field(name="Member Count", value=f"{guild.member_count}", inline=False)
        embed.set_footer(text=f"Total Guilds: {len(self.bot.guilds)}")
        embed.set_thumbnail(url=guild.icon.url)
        await self.send_webhook_message(webhook_url, embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.logger.info(f"Guild Remove: {guild.name} ({guild.id})")
        webhook_url = str(os.getenv('BOT_WEBHOOK_URL'))
        embed = discord.Embed(description=f"Left Server: **{guild.name}** \n({guild.id})" , color=discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.add_field(name="Owner", value=f"{guild.owner.name}", inline=False)
        embed.add_field(name="Member Count", value=f"{guild.member_count}", inline=False)
        embed.set_footer(text=f"Total Guilds: {len(self.bot.guilds)}")
        embed.set_thumbnail(url=guild.icon.url)
        await self.send_webhook_message(webhook_url, embed)

    async def cog_unload(self):
        await self.session.close()

async def setup(bot):
    await bot.add_cog(ServerJoinLogger(bot))