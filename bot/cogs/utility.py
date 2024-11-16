import discord
from discord import app_commands
from discord.ext import commands, tasks
import deep_translator
from deep_translator import GoogleTranslator, single_detection
import langcodes
import os
from dotenv import load_dotenv
import aiosqlite
import asyncio
from datetime import datetime, timedelta
import uuid
import pytz

load_dotenv()

reminders = "data/reminders.db"
notes = "data/notes.db"

class Utility(commands.GroupCog, name="utility"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="Translate to English",
            callback=self.Translate_to_English,
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_load(self) -> None:
        self.load_reminders.start()
        await self.notes_table()
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

    async def notes_table(self) -> None:
        async with aiosqlite.connect(notes) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    note TEXT
                )
            """)

    @tasks.loop()
    async def load_reminders(self) -> None:
        async with aiosqlite.connect(reminders) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    guild_id INTEGER,
                    user_id INTEGER,
                    channel_id INTEGER,
                    reminder TEXT,
                    remind_at TIMESTAMP,
                    id TEXT,
                    PRIMARY KEY (guild_id, user_id, id)
                )
            ''')
            await db.commit()
            async with db.execute("SELECT guild_id, user_id, channel_id, reminder, remind_at, id FROM reminders") as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    user_id, guild_id, channel_id, reminder, remind_at, id = row
                    # Convert remind_at to a datetime object with correct TZ
                    remind_at = datetime.fromisoformat(remind_at)
                    delay = (remind_at - datetime.now(pytz.utc)).total_seconds()
                    if delay <= 0:
                        await self.send_reminder(user_id, guild_id, channel_id, reminder, id)
        
            async with db.execute("SELECT guild_id, user_id, channel_id, reminder, remind_at, id FROM reminders ORDER BY remind_at LIMIT 1") as cursor:
                next_reminder = await cursor.fetchone()
                if next_reminder is None:
                    self.load_reminders.stop()
                    return
            # Use fromisoformat to parse and set the `sleep_until`
                user_id, guild_id, channel_id, reminder, remind_at, id = next_reminder
                next_remind_at = datetime.fromisoformat(remind_at)
                await discord.utils.sleep_until(next_remind_at)
                await self.send_reminder(user_id, guild_id, channel_id, reminder, id)

    @load_reminders.before_loop
    async def before_load_reminders(self) -> None:
        await self.bot.wait_until_ready()

    async def send_reminder(self, user_id, guild_id, channel_id, reminder, id) -> None:
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
            await db.execute("DELETE FROM reminders WHERE guild_id = ? AND user_id = ? AND channel_id = ? AND reminder = ? and id = ?",
                             (user_id, guild_id, channel_id, reminder, id))
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

    reminder = app_commands.Group(name="reminder", description="Commands for reminders")

    notes = app_commands.Group(name="notes", description="Commands for notes")

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

    @reminder.command(name="add", description="Set a reminder")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(reminder="The reminder to set", time="The time for the reminder (e.g., 1d, 3h or 30m)")
    async def reminder_add(self, interaction: discord.Interaction, time: str, *, reminder: str) -> None:
        try:
            reminder_id = str(uuid.uuid4())
            time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            time_value = int(time[:-1])
            time_unit = time[-1]
            if time_unit not in time_units:
                raise ValueError("Invalid time unit. Please use 's', 'm', 'h', or 'd'.")
            reminder_time = time_value * time_units[time_unit]
            remind_at = discord.utils.utcnow() + timedelta(seconds=reminder_time)
            embed = discord.Embed(title="Reminder Set", description=f"I will remind you about '{reminder}' in {time_value}{time_unit}.", color=discord.Color.green())
            embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            async with aiosqlite.connect(reminders) as db:
                await db.execute("INSERT INTO reminders (guild_id, user_id, channel_id, reminder, remind_at, id) VALUES (?, ?, ?, ?, ?, ?)",
                                (interaction.user.id, interaction.guild_id, interaction.channel_id, reminder, remind_at, reminder_id))
                await db.commit()
            if self.load_reminders.is_running():
                self.load_reminders.restart()
            else:
                self.load_reminders.start()
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)

    @reminder.command(name="list", description="List all your reminders")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    async def reminder_list(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(reminders) as db:
            async with db.execute("SELECT reminder, remind_at, id FROM reminders WHERE user_id = ?", (interaction.user.id,)) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    embed = discord.Embed(title="No Reminders Set", description="You have no reminders set.", color=discord.Color.green())
                    embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                    await interaction.response.send_message(embed=embed)
                    return
                embed = discord.Embed(title="Your Reminders", color=discord.Color.green())
                for row in rows:
                    reminder, remind_at, id = row
                    remind_at = datetime.strptime(remind_at, '%Y-%m-%d %H:%M:%S')
                    time_left = remind_at - datetime.now()
                    time_left_str = str(time_left).split('.')[0]
                    embed.add_field(name=f"Reminder ID: {id}", value=f"Reminder: {reminder}\nTime Left: {time_left_str}", inline=False)
                embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed)

    @reminder.command(name="delete", description="Delete a reminder")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(id="The ID of the reminder to delete")
    async def reminder_delete(self, interaction: discord.Interaction, id: str) -> None:
        async with aiosqlite.connect(reminders) as db:
            async with db.execute("SELECT reminder, remind_at FROM reminders WHERE user_id = ? AND id = ?", (interaction.user.id, id)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    embed = discord.Embed(title="Reminder Not Found", description=f"No reminder found with ID {id}.", color=discord.Color.red())
                    embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                    await interaction.response.send_message(embed=embed)
                    return
                reminder, remind_at = row
                remind_at = datetime.strptime(remind_at, '%Y-%m-%d %H:%M:%S')
                time_left = remind_at - datetime.now()
                time_left_str = str(time_left).split('.')[0]
                embed = discord.Embed(title="Reminder Deleted", description=f"I have deleted your reminder '{reminder}' that was set {time_left_str} ago.", color=discord.Color.green())
            await db.execute("DELETE FROM reminders WHERE user_id = ? AND id = ?", (interaction.user.id, id))
            await db.commit()
        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @notes.command(name="add", description="Add a note")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(note="The note to add")
    async def notes_add(self, interaction: discord.Interaction, note: str) -> None:
        note_id = str(uuid.uuid4())
        async with aiosqlite.connect(notes) as db:
            await db.execute("INSERT INTO notes (user_id, note, id) VALUES (?, ?, ?)", (interaction.user.id, note, note_id))
            await db.commit()
        embed = discord.Embed(title="Note Added", description=f"Your note '{note}' has been added.", color=discord.Color.green(), timestamp=discord.utils.utcnow())
        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @notes.command(name="list", description="List all your notes")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    async def notes_list(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(notes) as db:
            async with db.execute("SELECT note, id FROM notes WHERE user_id = ?", (interaction.user.id,)) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    embed = discord.Embed(title="No Notes Set", description="You have no notes set.", color=discord.Color.green())
                    embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                embed = discord.Embed(title="Your Notes", color=discord.Color.green())
                for row in rows:
                    note = row[0]
                    id = row[1]
                    embed.add_field(name=f"Note (id:{id})", value=f"{note}", inline=False)
                embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @notes.command(name="delete", description="Delete a note")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(id="The ID of the note to delete")
    async def notes_delete(self, interaction: discord.Interaction, id: str) -> None:
        async with aiosqlite.connect(notes) as db:
            async with db.execute("SELECT note, id FROM notes WHERE user_id = ? AND id = ?", (interaction.user.id, id)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    embed = discord.Embed(title="Note Not Found", description=f"No note found with ID {id}.", color=discord.Color.red())
                    embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                note, _ = row
                embed = discord.Embed(title="Note Deleted", description=f"Your note '{note}' has been deleted.", color=discord.Color.green(), timestamp=discord.utils.utcnow())
                embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                await db.execute("DELETE FROM notes WHERE user_id = ? AND id = ?", (interaction.user.id, id))
                await db.commit()
                await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot) -> None:
    await bot.add_cog(Utility(bot))