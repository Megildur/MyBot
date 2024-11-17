import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
from typing import Optional, Literal
import sympy

count = 'data/count.db'

class CountingCog(commands.GroupCog, name="count"):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.locks = {}
        self.bot_delete = {}

    async def cog_load(self) -> None:
        async with aiosqlite.connect(count) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS counting_authors (
                    guild_id INTEGER PRIMARY KEY,
                    author_id INTEGER
                )
            ''')
            await db.execute('''
            CREATE TABLE IF NOT EXISTS counting (
            guild_id INTEGER NOT NULL PRIMARY KEY, 
            channel_id INTEGER NOT NULL, 
            previous_message_id INTEGER, 
            current_number INTEGER,
            reset INTEGER,
            emoji TEXT,
            irregular_numbers INTEGER,
            talking_users INTEGER
            )
        ''')
            await db.commit()
        
    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if message.author == self.bot.user:
            return
        guild_id = message.guild.id
        if guild_id not in self.locks:
            self.locks[guild_id] = asyncio.Lock()
        async with self.locks[guild_id]:
            async with aiosqlite.connect(count) as db:
                cursor = await db.execute('SELECT channel_id, previous_message_id, current_number, reset, emoji, irregular_numbers, talking_users FROM counting WHERE guild_id=?', (guild_id,))
                row = await cursor.fetchone()
            if row:
                channel_id, previous_message_id, current_number, reset, emoji, irregular_numbers, talking_users = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
                async with aiosqlite.connect(count) as db:
                    cursor = await db.execute('SELECT author_id FROM counting_authors WHERE guild_id = ?', (message.guild.id,))
                    author_id = await cursor.fetchone()
                if message.channel.id == channel_id:
                    if talking_users == 0 or talking_users is None:
                        if author_id and author_id[0] == message.author.id:
                            await self.wait_count(message)
                            return
                        if not message.content.isnumeric():
                            await message.delete()
                            embed = discord.Embed(description='This channel is for counting only.', color=discord.Color.red())
                            await message.channel.send(embed=embed, delete_after=10)
                            return
                        if message.content.isnumeric():
                            if int(message.content) == current_number + 1:
                                num = int(message.content)
                                await self.process_message(message, num, emoji)
                    else:
                        if message.content.isnumeric():
                            if author_id and author_id[0] == message.author.id:
                                if int(message.content) == current_number + 1:
                                    await self.wait_count(message)
                                    return
                            num = int(message.content)
                            if num != current_number + 1:
                                await self.delete_message(message, reset)
                                return
                            await self.process_message(message, num, emoji)

    async def delete_message(self, message, reset) -> None:        
        await message.delete()
        if reset is None or reset == 0:
            embed = discord.Embed(description='That is the wrong number.', color=discord.Color.red())
        elif reset == 1:
            embed = discord.Embed(description='That is the wrong number. Count reset to 0!', color=discord.Color.red())
            async with aiosqlite.connect(count) as db:
                await db.execute('UPDATE counting SET current_number = 0 WHERE guild_id = ?', (message.guild.id,))
                await db.commit()
        await message.channel.send(embed=embed, delete_after=10)

    async def process_message(self, message, num, emoji) -> None:
        async with aiosqlite.connect(count) as db:
            await db.execute('UPDATE counting SET current_number = ?, previous_message_id = ? WHERE guild_id = ?', (num, message.id, message.guild.id))
            await db.execute('UPDATE counting_authors SET author_id =? WHERE guild_id =?', (message.author.id, message.guild.id))
            await db.commit()
            if emoji is None or emoji == 0:
                await message.add_reaction('✅')
            else:
                await message.add_reaction(emoji)

    async def wait_count(self, message) -> None:
        await message.delete()
        embed = discord.Embed(description='You must wait for another person to count first.', color=discord.Color.red())
        await message.channel.send(embed=embed, delete_after=10)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after) -> None:
        if before.author == self.bot.user:
            return
        async with aiosqlite.connect(count) as db:
            cursor = await db.execute('SELECT * FROM counting WHERE guild_id =?', (before.guild.id,))
            row = await cursor.fetchone()
        if row:
            channel_id, previous_message_id, current_number, emoji = row[1], row[2], row[3], row[5]
            if before.channel.id == channel_id and before.id == previous_message_id and after.content != str(current_number):
                channel_id = after.channel.id
                if channel_id not in self.bot_delete:
                    self.bot_delete[channel_id] = []
                self.bot_delete[channel_id].append(after.id)
                await after.delete()
                bot_message = await before.channel.send(str(current_number))
                if emoji is None or emoji == 0:
                    await bot_message.add_reaction('✅')
                else:
                    await bot_message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_message_delete(self, message) -> None:
        if message.author == self.bot.user:
            return
        channel_id = message.channel.id
        if channel_id in self.bot_delete:
            if message.id in self.bot_delete[channel_id]:
                self.bot_delete[channel_id].remove(message.id)
                return
        async with aiosqlite.connect(count) as db:
            cursor = await db.execute('SELECT * FROM counting WHERE guild_id =?', (message.guild.id,))
            row = await cursor.fetchone()
        if row:
            channel_id, previous_message_id, current_number, emoji = row[1], row[2], row[3], row[5]
            if message.channel.id == channel_id and message.id == previous_message_id:
                bot_message = await message.channel.send(str(current_number))
                if emoji is None or emoji == 0:
                    await message.add_reaction('✅')
                else:
                    await message.add_reaction(emoji)

    @app_commands.command(name='channel', description='Set counting channel')
    @app_commands.default_permissions(manage_channels=True)
    async def channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        async with aiosqlite.connect(
            count
        ) as self.db: 
            async with self.db.execute('SELECT * FROM counting WHERE guild_id =?', (interaction.guild_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    await self.db.execute('UPDATE counting SET channel_id =? WHERE guild_id =?', (channel.id, interaction.guild_id))
                else:
                    await self.db.execute('INSERT OR REPLACE INTO counting (guild_id, channel_id, previous_message_id, current_number) VALUES (?,?,?,?)', (interaction.guild_id, channel.id, None, 0))
                await self.db.commit()
            async with self.db.execute('SELECT author_id FROM counting_authors WHERE guild_id =?', (interaction.guild_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    await self.db.execute('UPDATE counting_authors SET author_id =? WHERE guild_id =?', (None, interaction.guild_id))
                else:
                    await self.db.execute('INSERT OR REPLACE INTO counting_authors (guild_id, author_id) VALUES (?,?)', (interaction.guild_id, None))
                await self.db.commit()
            embed = discord.Embed(description=f'Counting channel set to {channel.mention}', color=discord.Color.green())
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name='reset',description='reset count to zero or chosen number')
    @app_commands.describe(number='number to reset to(leave blank to reset to 0)')
    @app_commands.default_permissions(manage_channels=True)
    async def count_reset(self, interaction: discord.Interaction, number: int = 0) -> None:
        async with aiosqlite.connect(count) as db:
            cursor = await db.execute('''SELECT current_number FROM counting WHERE guild_id =?''', (interaction.guild_id,))
            num = await cursor.fetchone()
            if number == 0 and num == 0:
                embed = discord.Embed(title='Error', description='Cannot reset! Count is already at 0', color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            else:
                await db.execute('''
                    UPDATE counting SET previous_message_id =?, current_number =? WHERE guild_id =?''', (None, number, interaction.guild_id))
                await db.commit()
                embed = discord.Embed(title='Success', description=f'Count has been reset to {number}', color=discord.Color.green())
                await interaction.response.send_message(embed=embed)

    @app_commands.command(name='emoji', description='Set counting emoji')
    @app_commands.describe(emoji='emoji to use')
    @app_commands.default_permissions(manage_channels=True)
    async def count_emoji(self, interaction: discord.Interaction, emoji: str) -> None:
        async with aiosqlite.connect(count) as db:
            await db.execute('UPDATE counting SET emoji =? WHERE guild_id =?', (emoji, interaction.guild_id))
            await db.commit()
        embed = discord.Embed(title='Success', description=f'Counting emoji set to {emoji}', color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='irregular', description='Set to allow counting with irregular numbers')
    @app_commands.describe(enable='enable or disable')
    @app_commands.default_permissions(manage_channels=True)
    async def count_irregular(self, interaction: discord.Interaction, enable: Literal['enable', 'disable']) -> None:
        async with aiosqlite.connect(count) as db:
            if enable == 'enable':
                await db.execute('UPDATE counting SET irregular_numbers =? WHERE guild_id =?', (1, interaction.guild_id))
            else:
                await db.execute('UPDATE counting SET irregular_numbers =? WHERE guild_id =?', (0, interaction.guild_id))
            await db.commit()
        embed = discord.Embed(title='Success', description=f'Irregular numbers set to {enable}', color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='talking', description='Set to allow counting with talking users')
    @app_commands.describe(enable='enable or disable')
    @app_commands.default_permissions(manage_channels=True)
    async def count_talking(self, interaction: discord.Interaction, enable: Literal['enable', 'disable']) -> None:
        async with aiosqlite.connect(count) as db:
            if enable == 'enable':
                await db.execute('UPDATE counting SET talking_users =? WHERE guild_id =?', (1, interaction.guild_id))
            else:
                await db.execute('UPDATE counting SET talking_users =? WHERE guild_id =?', (0, interaction.guild_id))
            await db.commit()
        embed = discord.Embed(title='Success', description=f'Talking users set to {enable}', color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='auto_reset', description='Set counting to auto reset count when a user sends a wrong number')
    @app_commands.describe(enable='enable or disable')
    @app_commands.default_permissions(manage_channels=True)
    async def count_auto_reset(self, interaction: discord.Interaction, enable: Literal['enable', 'disable' ]) -> None:
        async with aiosqlite.connect(count) as db:
            if enable == 'enable':
                await db.execute('UPDATE counting SET reset =? WHERE guild_id =?', (1, interaction.guild_id))
            else:
                await db.execute('UPDATE counting SET reset =? WHERE guild_id =?', (0, interaction.guild_id))
            await db.commit()
        embed = discord.Embed(title='Success', description=f'Auto reset set to {enable}', color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='current_settings', description='View current counting settings')
    async def count_settings(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(count) as db:
            cursor = await db.execute('SELECT channel_id, previous_message_id, current_number, emoji, irregular_numbers, talking_users, reset FROM counting WHERE guild_id =?', (interaction.guild_id,))
            row = await cursor.fetchone()
        if row:
            channel_id, previous_message_id, current_number, emoji, irregular_numbers, talking_users, reset = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
            embed = discord.Embed(title='Current Settings', color=discord.Color.green())
            embed.add_field(name='Channel', value=f'<#{channel_id}>')
            if emoji:
                embed.add_field(name='Emoji', value=emoji)
            if irregular_numbers is None or irregular_numbers == 0:
                embed.add_field(name='Irregular Numbers', value='Disabled')
            if irregular_numbers == 1:
                embed.add_field(name='Irregular Numbers', value='Enabled')
            if talking_users is None or talking_users == 0:
                embed.add_field(name='Talking Users', value='Disabled')
            if talking_users == 1:
                embed.add_field(name='Talking Users', value='Enabled')
            if reset is None or reset == 0:
                embed.add_field(name='Auto Reset', value='Disabled')
            if reset == 1:
                embed.add_field(name='Auto Reset', value='Enabled')
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title='Error', description='No counting channel set', color=discord.Color.red())
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(CountingCog(bot))