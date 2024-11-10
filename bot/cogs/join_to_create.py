import discord
from discord.ext import commands
import aiosqlite
from discord import app_commands
from typing import Optional, Literal
from bot.utils.mod_helpers import bot_has_permission

jtc = "data/jtc.db"

class JoinToCreateCog(commands.GroupCog, name="jtc"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.created = {}

    async def cog_load(self) -> None:
        async with aiosqlite.connect(jtc) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS join_to_create (
                guild_id INTEGER NOT NULL,
                channel_name TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, channel_name, channel_id, category_id)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS created (
                guild_id INTEGER NOT NULL,
                channel_name TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, channel_name)
                )
            ''')
            await db.commit()
            await db.close()

    @app_commands.command(
        name='add', 
        description='Create a join to create channel'
    )
    @app_commands.describe(channel_catagory='The catagory to create the channel in', create_new_channel='Name to give new join ti create channel', use_existing_channel='Use an existing channel instead of creating a new one')
    @app_commands.default_permissions(manage_channels=True)
    async def join_to_create_create(
        self, 
        interaction,
        channel_category: discord.CategoryChannel,
        create_new_channel: Optional[str] = None,
        use_existing_channel: Optional[discord.VoiceChannel] = None
    ) -> None:
        if create_new_channel and use_existing_channel is not None:
            embed = discord.Embed(
                title='Error', description='You can only provide one of the following options: `create_new_channel` or `use_existing_channel`', color=discord.Color.red())
            await interaction.response.send_message(
                embed=embed, 
                ephemeral=True
            )
            return
        elif create_new_channel is None and use_existing_channel is None:
            embed = discord.Embed(
                title='Error', description='You must provide one of the following options: `create_new_channel` or `use_existing_channel`', color=discord.Color.red())
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )    
            return
        if use_existing_channel:
            if use_existing_channel.category != channel_category:
                embed = discord.Embed(
                    title='Error', description='The channel you selected in not in the category you selected!', color=discord.Color.red())
                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )
                return
            async with aiosqlite.connect(jtc) as db:
                async with db.execute('SELECT channel_id FROM join_to_create WHERE guild_id = ?', (interaction.guild.id)) as cursor:
                    result = await cursor.fetchall()
                if result:
                    for row in result:
                        if use_existing_channel.id == row[0]:
                            embed = discord.Embed(
                            title='Error', description='This channel is already a join to create channel', color=discord.Color.red())
                            await interaction.response.send_message(
                                embed=embed,
                                ephemeral=True
                            )
                            return
                        else:
                            await db.execute('INSERT INTO join_to_create VALUES (?, ?, ?, ?)', (interaction.guild_id, use_existing_channel.name, use_existing_channel.id, channel_category.id))
                            await db.commit()
                            embed = discord.Embed(title='Join to create channel created', description=f'Created join to create channel {use_existing_channel.mention} in category {channel_category.mention}', color=discord.Color.green())
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                            return
                else:
                    await db.execute('INSERT INTO join_to_create VALUES (?, ?, ?, ?)', (interaction.guild_id, use_existing_channel.name, use_existing_channel.id, channel_category.id))
                    await db.commit()
                    embed = discord.Embed(title='Join to create channel created', description=f'Created join to create channel {use_existing_channel.mention} in category {channel_category.mention}', color=discord.Color.green())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
        else:
            existing_channel = discord.utils.get(interaction.guild.voice_channels, name=create_new_channel, category=channel_category)
            if existing_channel is not None:
                embed = discord.Embed(
                    title='Error', description='A channel with that name already exists in that category', color=discord.Color.red())
                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )
                return
            channel = await interaction.guild.create_voice_channel(
                name=create_new_channel, 
                category=channel_category
            )
            async with aiosqlite.connect(jtc) as db:
                await db.execute(
                    'INSERT INTO join_to_create VALUES (?, ?, ?, ?)', 
                     (interaction.guild_id, create_new_channel, channel.id, channel_category.id)
                )
                await db.commit()
                embed = discord.Embed(
                    title='Join to create channel created', description=f'Created join to create channel {channel.mention} in category {channel_category.mention}', color=discord.Color.green()
                )
                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )

    @app_commands.command(name='remove', description='Delete a join to create channel')
    @app_commands.describe(channel_category='The category of the channel to delete', channel='The name of the channel to delete', delete_channel='do you want to delte the channel from the server')
    @app_commands.default_permissions(manage_channels=True)
    async def delete(
        self, 
        interaction, 
        channel_category: discord.CategoryChannel,
        channel: discord.VoiceChannel,
        delete_channel: Literal['Yes', 'No'] = 'Yes'
    ) -> None:
        if channel.category != channel_category:
            embed = discord.Embed(
                title='Error', description='The channel you selected in not in the category you selected!', color=discord.Color.red())
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            return
        async with aiosqlite.connect(jtc) as db:
            async with db.execute('SELECT channel_id FROM join_to_create WHERE guild_id = ?', (interaction.guild.id)) as cursor:
                result = await cursor.fetchall()
                if result:
                    for row in result:
                        if channel.id != row[0]:
                            embed = discord.Embed(title='Error', description='This channel is not a join to create channel', color=discord.Color.red())
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                            return
                        else:
                            if delete_channel == 'Yes':
                                if await bot_has_permission(interaction, "manage_channels"):
                                    await channel.delete()
                                else:
                                    embed = discord.Embed(title='Error', description='I do not have the required permissions to delete channels. Please give me manage channels permissions and run the command again.', color=discord.Color.red())
                                    await interaction.response.send_message(embed=embed, ephemeral=True)
                                    return
                            async with aiosqlite.connect(jtc) as db:
                                await db.execute('DELETE FROM join_to_create WHERE guild_id = ? AND channel_name = ?', (interaction.guild_id, channel.name))
                                await db.commit()
                                embed = discord.Embed(title='Join to create channel deleted', description=f'Deleted join to create channel {channel.mention} in category {channel_category.mention}', color=discord.Color.green())
                                await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(title='Error', description='This channel is not a join to create channel', color=discord.Color.red())
                    await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='list', description='List all join to create channels')
    async def list(self, interaction):
        async with aiosqlite.connect(jtc) as db:
            async with db.execute('SELECT channel_id FROM join_to_create WHERE guild_id = ?', (interaction.guild.id)) as cursor:
                result = await cursor.fetchall()
        if not result:
            embed = discord.Embed(title='Error', description='There are no join to create channels', color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        else:
            channels = [f'<#{channel_id}>' for channel_id in [row[0] for row in result]]
            embed = discord.Embed(title='Join to create channels', description='\n'.join(channels), color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def created_channel_db(self, guild_id):
        async with aiosqlite.connect(jtc) as db:
            cursor = await db.execute('''
                SELECT * FROM created WHERE guild_id = ?
            ''', (guild_id,))
            data = await cursor.fetchall()
            if data:
                self.created[guild_id]['channel_name'] = [row[1] for row in data]
                self.created[guild_id]['channel_id'] = [row[2] for row in data]
            else:
                self.created[guild_id]['channel_name'] = []
                self.created[guild_id]['channel_id'] = []
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel is not None:
            async with aiosqlite.connect(jtc) as db:
                async with db.execute('SELECT channel_id FROM join_to_create WHERE guild_id = ?', (member.guild.id,)) as cursor:
                    result = await cursor.fetchall()
            if after.channel.id in [row[0] for row in result]:
                new_channel = await member.guild.create_voice_channel(
                    f'{member.display_name}\'s Channel',
                    category=after.channel.category
                )
                if member.guild.id not in self.created:
                    self.created[member.guild.id] = {}
                    await self.created_channel_db(member.guild.id)
                self.created[member.guild.id]['channel_name'].append(new_channel.name)
                self.created[member.guild.id]['channel_id'].append(new_channel.id)
                async with aiosqlite.connect("data/jtc.db") as db:
                    await db.execute(
                        'INSERT INTO created VALUES (?, ?, ?)',
                        (member.guild.id, new_channel.name, new_channel.id)
                    )
                    await db.commit()
                await member.move_to(new_channel)
        if before.channel is not None:
            if member.guild.id not in self.created:
                self.created[member.guild.id] = {}
                await self.created_channel_db(member.guild.id)
            if before.channel.id in self.created[member.guild.id]['channel_id']:
                if len(before.channel.members) == 0:
                    await before.channel.delete()
                    self.created[member.guild.id]['channel_name'].remove(before.channel.name)
                    self.created[member.guild.id]['channel_id'].remove(before.channel.id)
                    async with aiosqlite.connect("data/jtc.db") as db:
                        await db.execute(
                            'DELETE FROM created WHERE guild_id = ? AND channel_id = ?',
                            (before.channel.guild.id, before.channel.id)
                        )
                        await db.commit()

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.category != after.category:
            async with aiosqlite.connect("data/jtc.db") as db:
                async with db.execute('SELECT channel_id FROM join_to_create WHERE guild_id = ?', (before.guild.id,)) as cursor:
                    result = await cursor.fetchall()
                if before.id in [row[0] for row in result]:
                    await db.execute(
                        'UPDATE join_to_create SET category_id = ? WHERE channel_id = ?',
                        (after.category.id, before.id)
                    )
                    await db.commit()
        if before.name != after.name:
            async with aiosqlite.connect("data/jtc.db") as db:
                async with db.execute('SELECT channel_name FROM join_to_create WHERE guild_id = ?', (before.guild.id,)) as cursor:
                    result = await cursor.fetchall()
            if before.name in [row[0] for row in result]:
                await db.execute(
                    'UPDATE join_to_create SET channel_name = ? WHERE channel_id = ?',
                    (after.name, before.id)
                )
                await db.commit()
                
async def setup(bot):
    await bot.add_cog(JoinToCreateCog(bot))