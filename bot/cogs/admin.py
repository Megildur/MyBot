import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import asyncio
from datetime import datetime, timedelta

persistent_data = "data/persistent_data.db"

class Admin(commands.GroupCog, group_name="admin"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.ping_message_id = {}
        self.ping_channel_id = {}
        self.log_channel_id = {}
        self.update_ping.start()

    async def cog_load(self) -> None:
        await self.load_message_info()
        await self.load_log_channel()
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.tree_on_error

    async def cog_unload(self) -> None:
        status = "Bot is offline"
        await self.update_status(status)
        self.update_ping.cancel()
        tree = self.bot.tree
        tree.on_error = self._old_tree_error

    async def tree_on_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_after = int(error.retry_after)
            if retry_after < 60:
                retry_after = f"{retry_after} seconds"
            else:
                retry_after = f"{retry_after // 60} minutes"
            embed = discord.Embed(
                title="Command Cooldown",
                description=f"This command is on cooldown. Please try again in {retry_after}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            print(f"An error occurred: {error}")
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

    async def update_status(self, status) -> None:
        for guild_id in self.ping_channel_id.keys():
            channel_id = self.ping_channel_id.get(guild_id)
            message_id = self.ping_message_id.get(guild_id)
            if channel_id and message_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    try:
                        msg = await channel.fetch_message(message_id)
                        if msg and msg.embeds:
                            footer = msg.embeds[0]
                            footer_content = footer.footer
                            embed = self.update_ping_embed(footer_content, status)
                            await msg.edit(embed=embed)
                    except discord.NotFound:
                        pass
            await asyncio.sleep(5)

    async def load_message_info(self) -> None:
        async with aiosqlite.connect(persistent_data) as db:
            async with db.execute("CREATE TABLE IF NOT EXISTS ping_info (guild_id INTEGER, message_id INTEGER, channel_id INTEGER)") as cursor:
                await db.commit()
            async with db.execute("SELECT guild_id, message_id, channel_id FROM ping_info") as cursor:
                rows = await cursor.fetchall()
                if rows:
                    for row in rows:                            
                        self.ping_message_id[row[0]] = row[1]
                        self.ping_channel_id[row[0]] = row[2]

    async def load_log_channel(self) -> None:
        async with aiosqlite.connect(persistent_data) as db:
            async with db.execute("CREATE TABLE IF NOT EXISTS log_channel (guild_id INTEGER, channel_id INTEGER)") as cursor:
                await db.commit()
            async with db.execute("SELECT guild_id, channel_id FROM log_channel") as cursor:
                rows = await cursor.fetchall()
                if rows:
                    for row in rows:
                        self.log_channel_id[row[0]] = row[1]

    async def save_message_info(self, message_id, channel_id, guild_id) -> None:
        async with aiosqlite.connect(persistent_data) as db:
            await db.execute("DELETE FROM ping_info WHERE guild_id = ?", (guild_id,))
            await db.execute("INSERT OR REPLACE INTO ping_info (guild_id, message_id, channel_id) VALUES (?, ?, ?)", (guild_id, message_id, channel_id))
            await db.commit()

    async def save_log_channel(self, channel_id, guild_id) -> None:
        async with aiosqlite.connect(persistent_data) as db:
            await db.execute("DELETE FROM log_channel WHERE guild_id = ?", (guild_id,))
            await db.execute("INSERT OR REPLACE INTO log_channel (guild_id, channel_id) VALUES (?, ?)", (guild_id, channel_id))
            await db.commit()

    def create_ping_embed(self, interaction) -> discord.Embed:
        ping = round(self.bot.latency * 1000)
        next_update = datetime.utcnow() + timedelta(minutes=30)
        timestamp = int(next_update.timestamp())
        embed = discord.Embed(title="Bot Ping", color=discord.Color.green(), timestamp=discord.utils.utcnow())
        embed.add_field(name="Ping", value=f"{ping}ms", inline=True)
        embed.add_field(name="Next Update", value=f'<t:{timestamp}:R>', inline=True)
        embed.add_field(name="Status", value="Bot is online", inline=True)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    def update_ping_embed(self, footer_content, status) -> discord.Embed:
        ping = round(self.bot.latency * 1000)
        next_update = datetime.utcnow() + timedelta(minutes=30)
        timestamp = int(next_update.timestamp())
        embed = discord.Embed(title="Bot Ping", color=discord.Color.green(), timestamp=discord.utils.utcnow())
        embed.add_field(name="Ping", value=f"{ping}ms", inline=True)
        embed.add_field(name="Next Update", value=f'<t:{timestamp}:R>', inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        embed.set_footer(text=footer_content.text, icon_url=footer_content.icon_url)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    @tasks.loop(minutes=30)
    async def update_ping(self) -> None:
        for guild_id in self.ping_channel_id.keys():
            channel_id = self.ping_channel_id.get(guild_id)
            message_id = self.ping_message_id.get(guild_id)

            if channel_id and message_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    try:
                        msg = await channel.fetch_message(message_id)
                        if msg and msg.embeds:
                            footer = msg.embeds[0]
                            footer_content = footer.footer
                            status = "Bot is online"
                            embed = self.update_ping_embed(footer_content, status)
                            await msg.edit(embed=embed)
                    except discord.NotFound:
                        pass
            await asyncio.sleep(2)

    @update_ping.before_loop
    async def before_update_ping(self):
        await self.bot.wait_until_ready()

    def get_log_channel_id(self, guild_id):
        return self.log_channel_id.get(guild_id, None)

    @app_commands.command(name="ping", description="Set the ping message")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 300, key=lambda i: (i.guild_id, i.user.id))
    async def ping(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild_id
        embed = self.create_ping_embed(interaction)
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        self.ping_message_id[guild_id] = msg.id
        self.ping_channel_id[guild_id] = msg.channel.id
        await self.save_message_info(self.ping_message_id[guild_id], self.ping_channel_id[guild_id], guild_id)

    @app_commands.command(name="setlogchannel", description="Set the log channel")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="The channel to set as the log channel for moderation actions")
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        guild_id = interaction.guild_id
        self.log_channel_id[guild_id] = channel.id
        await self.save_log_channel(self.log_channel_id[guild_id], guild_id)
        embed = discord.Embed(title="Log Channel Set", description=f"The log channel has been set to {channel.mention}", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
async def setup(bot) -> None:
    admin_cog = Admin(bot)
    await bot.add_cog(admin_cog)
    bot.admin_cog = admin_cog