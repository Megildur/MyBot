import discord
from discord import app_commands
from discord.ext import commands
import deep_translator
from deep_translator import GoogleTranslator, single_detection
import langcodes
import os
from dotenv import load_dotenv
import aiosqlite
import asyncio
from datetime import datetime, timedelta

load_dotenv()

reminders = "data/reminders.db"

class Utility(commands.GroupCog, name="utility"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="Translate to English",
            callback=self.Translate_to_English,
        )
        self.bot.tree.add_command(self.ctx_menu)
        self.bot.loop.create_task(self.load_reminders())

    async def cog_load(self) -> None:
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.tree_on_error
        
    async def cog_unload(self) -> None:
        tree = self.bot.tree
        tree.on_error = self._old_tree_error
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    async def tree_on_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_after = int(error.retry_after)
            embed = discord.Embed(
                title="Command Cooldown",
                description=f"This command is on cooldown. Please try again in {retry_after} seconds.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            print(f"An error occurred: {error}")
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

    async def load_reminders(self):
        async with aiosqlite.connect(reminders) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    user_id INTEGER,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    reminder TEXT,
                    remind_at TIMESTAMP
                )
            ''')
            await db.commit()
            async with db.execute("SELECT user_id, guild_id, channel_id, reminder, remind_at FROM reminders") as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    user_id, guild_id, channel_id, reminder, remind_at = row
                    remind_at = datetime.strptime(remind_at, '%Y-%m-%d %H:%M:%S')
                    delay = (remind_at - datetime.now()).total_seconds()
                    if delay > 0:
                        self.bot.loop.create_task(self.send_reminder(user_id, guild_id, channel_id, reminder, delay))
                    else:
                        self.bot.loop.create_task(self.send_reminder(user_id, guild_id, channel_id, reminder, 0))

    async def send_reminder(self, user_id, guild_id, channel_id, reminder, delay):
        await asyncio.sleep(delay)
        guild = self.bot.get_guild(guild_id)
        channel = guild.get_channel(channel_id)
        user = guild.get_member(user_id)
        if channel:
            embed = discord.Embed(
                title="Reminder",
                description=f" Here is your reminder: \n\n {reminder}",
                color=discord.Color.green(),
                timestamp = discord.utils.utcnow()
            )
            embed.set_thumbnail(url=user.avatar.url)
            await channel.send(f"{user.mention}", embed=embed)
        async with aiosqlite.connect(reminders) as db:
            await db.execute("DELETE FROM reminders WHERE user_id = ? AND guild_id = ? AND channel_id = ? AND reminder = ?",
                             (user_id, guild_id, channel_id, reminder))
            await db.commit()

    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.checks.cooldown(2, 20, key=lambda i: (i.guild_id, i.user.id))
    async def Translate_to_English(self, interaction: discord.Interaction, message: discord.Message) -> None:
        try:
            translator = GoogleTranslator(source='auto', target='en')
            translation = translator.translate(message.content)
            source_language = single_detection(message.content, api_key=str(os.getenv('API_KEY')))
            language = langcodes.get(source_language).language_name()
            embed = discord.Embed(title="Translation", description=f"**Original Text:** {message.content}\n**Translated Text:** {translation}\n**Language:** {language}", color=discord.Color.green())
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(e)
            embed = discord.Embed(title="Translation Error", description=f"An error occurred while translating the message.\nException: {e}", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="member_count", description="Get the total member count of the server")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    async def member_count(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Total member count: {interaction.guild.member_count}")

    @app_commands.command(name="human_member_count", description="Get the member count of the server excluding bots")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    async def human_member_count(self, interaction: discord.Interaction) -> None:
        human_members = [member for member in interaction.guild.members if not member.bot]
        await interaction.response.send_message(f"Human member count: {len(human_members)}")

    @app_commands.command(name="ping", description="Get the bot's latency")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    async def ping(self, interaction: discord.Interaction) -> None:
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(title="Ping", description=f"Pong! Latency: {latency}ms", color=discord.Color.green())
        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        embed.timestamp = discord.utils.utcnow()
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reminder", description="Set a reminder")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    async def reminder(self, interaction: discord.Interaction, time: str, *, reminder: str) -> None:
        try:
            time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            time_value = int(time[:-1])
            time_unit = time[-1]
            if time_unit not in time_units:
                raise ValueError("Invalid time unit. Please use 's', 'm', 'h', or 'd'.")
            reminder_time = time_value * time_units[time_unit]
            remind_at = datetime.now() + timedelta(seconds=reminder_time)
            embed = discord.Embed(title="Reminder Set", description=f"I will remind you about '{reminder}' in {time_value}{time_unit}.", color=discord.Color.green())
            embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            async with aiosqlite.connect(reminders) as db:
                await db.execute("INSERT INTO reminders (user_id, guild_id, channel_id, reminder, remind_at) VALUES (?, ?, ?, ?, ?)",
                                (interaction.user.id, interaction.guild_id, interaction.channel_id, reminder, remind_at.strftime('%Y-%m-%d %H:%M:%S')))
                await db.commit()
            self.bot.loop.create_task(self.send_reminder(interaction.user.id, interaction.guild_id, interaction.channel_id, reminder, reminder_time))
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)

async def setup(bot) -> None:
    await bot.add_cog(Utility(bot))