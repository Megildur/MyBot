import discord
from discord.ext import commands
import aiosqlite
from discord import app_commands
from discord.app_commands import Choice
import re
from typing import Optional
from bot.utils.variablesmo import color_map

modb = "data/media_only.db"
moedb = "data/media_only_embeds.db"

@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
class MediaOnlyCog(commands.GroupCog, group_name='media_only'):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        async with aiosqlite.connect(modb) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS media_only_channels (
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, channel_id)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS threads (
                guild_id INTEGER NOT NULL,
                enabled INTEGER NOT NULL,
                PRIMARY KEY (guild_id)
                )
            ''')
            await db.commit()
        async with aiosqlite.connect(moedb) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS MO_embed (
                guild_id INTEGER NOT NULL PRIMARY KEY,
                custom_embed INTEGER NOT NULL,
                embed_title TEXT,
                embed_description TEXT,
                embed_color TEXT,
                embed_image TEXT,
                embed_thumbnail TEXT,
                embed_footer TEXT
                )
            ''')
            await db.commit()
        
    @app_commands.command(name="add", description="Add a channel to the media only channels")
    @app_commands.describe(channel="The channel to add. Leave blank to add the hannel the command is used in.")
    @app_commands.default_permissions(manage_channels=True)
    async def set_media_only(self, interaction, channel: Optional[discord.TextChannel] = None) -> None:
        if channel == None:
            channel = interaction.channel
        guild_id = interaction.guild_id
        async with aiosqlite.connect(modb) as db:
            async with db.execute('SELECT * FROM media_only_channels WHERE guild_id = ? AND channel_id = ?', (guild_id, channel.id)) as cursor:
                result = await cursor.fetchone()
                if result:
                    embed = discord.Embed(title="Error", description=f"Channel {channel.mention} is already in the media only channels.", color=discord.Color.red())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await db.execute("INSERT INTO media_only_channels (guild_id, channel_id) VALUES (?, ?)", (guild_id, channel.id))
                    await db.commit()
                    embed = discord.Embed(title="Media Only Channel Added", description=f"The channel {channel.mention} has been added to the media only channels list.", color=discord.Color.green())
                    await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="remove", description="Remove a channel from the media only channels")
    @app_commands.describe(channel="The channel to remove. Leave blank to remove the channel the command is used in.")
    @app_commands.default_permissions(manage_channels=True)
    async def remove_media_only(self, interaction, channel: Optional[discord.TextChannel] = None) -> None:
        if channel == None:
            channel = interaction.channel
        guild_id = interaction.guild_id
        async with aiosqlite.connect(modb) as db:
            async with db.execute('SELECT * FROM media_only_channels WHERE guild_id = ? AND channel_id = ?', (guild_id, channel.id)) as cursor:
                result = await cursor.fetchone()
                if not result:
                    embed = discord.Embed(title="Error", description=f"{channel.mention} is not in the media only channels list.", color=discord.Color.red())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await db.execute("DELETE FROM media_only_channels WHERE guild_id = ? AND channel_id = ?", (guild_id, channel.id))
                    await db.commit()
                    embed = discord.Embed(title="Media Only Channel Removed", description=f"Removed {channel.mention} from the media only channels list.", color=discord.Color.green())
                    await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="embed", description="Set the warning embed for media only channels")
    @app_commands.describe(action="Set wmbed to default or custom")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.choices(
        action = [
            Choice(name="Set to custom", value=1),
            Choice(name="Set to default", value=0)
        ]
    )
    async def set_embed(self, interaction, action: Choice[int]) -> None:
        guild_id = interaction.guild_id
        async with aiosqlite.connect(moedb) as db:
            async with db.execute('SELECT embed_title, embed_description, embed_color, embed_image, embed_thumbnail, embed_footer FROM MO_embed WHERE guild_id = ?', (guild_id,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    if action.value == 1:
                        embed = discord.Embed(title="Media Only Embed Already Set", description=f"The media only embed has already been set to custom. You may edit your custom embed below", color=discord.Color.green())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        if result[0] != None:
                            title = result[0]
                        if result[1] != None:
                            description = result[1]
                        if result[2] != None:
                            color = color_map[result[2]]
                        else:
                            color = discord.Color.red()
                        eembed = discord.Embed(title=title, description=description, color=color)
                        if result[3]:
                            eembed.set_image(url=result[3])
                        if result[4]:
                            eembed.set_thumbnail(url=result[4])
                        if result[5]:
                            eembed.set_footer(text=result[5])
                        await interaction.followup.send(embed=eembed, ephemeral=True, view=EmbedBuilder())
                    else:
                        await db.execute("DELETE FROM MO_embed WHERE guild_id = ?", (guild_id,))
                        await db.commit()
                        embed = discord.Embed(title="Media Only Embed Set", description=f"The media only embed has been {action.name}.", color=discord.Color.green())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    if action.value == 1:
                         await db.execute("INSERT OR REPLACE INTO MO_embed (guild_id, custom_embed, embed_color) VALUES (?, ?, ?)", (guild_id, action.value, "discord.Color.red()"))
                         await db.commit()
                         embed = discord.Embed(title="Media Only Embed Set", description=f"The media only embed has been {action.name}.", color=discord.Color.green())
                         embed.add_field(name="Edit warning embed in the message below", value="Press the buttons to change the corrssponding field of the embed.(note:title and description must be set or the message will not send. all other fields are optional)")
                         await interaction.response.send_message(embed=embed, ephemeral=True)
                         eembed = discord.Embed(title="This is the title", description="This is the description", color=discord.Color.red())
                         eembed.set_image(url=interaction.guild.icon.url)
                         eembed.set_thumbnail(url=interaction.guild.me.avatar.url)
                         eembed.set_footer(text="This is the footer")
                         await interaction.followup.send(embed=eembed, view=EmbedBuilder(), ephemeral=True)
                    else:
                        embed = discord.Embed(title="Media Only Embed Already Set", description=f"The media only embed has already been set to default.", color=discord.Color.green())
                        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="list_settings", description="List all the media only channels and embed settings")
    async def list_media_only(self, interaction) -> None:
        guild_id = interaction.guild_id
        async with aiosqlite.connect(modb) as db:
            async with db.execute('SELECT channel_id FROM media_only_channels WHERE guild_id = ?', (guild_id,)) as cursor:
                result = await cursor.fetchall()
            async with db.execute('SELECT enabled FROM threads WHERE guild_id = ?', (guild_id,)) as cursor:
                result2 = await cursor.fetchone()
                if not result:
                    embed = discord.Embed(title="Media Only Channels List", description="There are no media only channels set up.", color=discord.Color.yellow())
                    embed.set_footer(text="Use '/media_only remove' to remove a channel from the list. Use '/media_only add' to add a channel to the list. Use '/media_only embed' to set a custom warning message embed.")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                else:
                    channels = [f"<#{channel_id}>" for channel_id in [channel[0] for channel in result]]
                    embed = discord.Embed(title="Media Only Channels List", description="\n".join(channels), color=discord.Color.yellow())
                    if result2[0] == 1:
                        embed.add_field(name="Auto-Threads Enabled", value="Change this setting with '/media_only auto_threads'")
                    else:
                        embed.add_field(name="Auto-Threads Disabled", value=f"Change this setting with '/media_only auto_threads'")
                    embed.set_footer(text="Use '/media_only remove' to remove a channel from the list. Use '/media_only add' to add a channel to the list. Use '/media_only embed' to set a custom warning message embed.")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
        async with aiosqlite.connect(moedb) as db:
            async with db.execute('SELECT embed_title, embed_description, embed_color, embed_image, embed_thumbnail, embed_footer FROM MO_embed WHERE guild_id = ?', (guild_id,)) as cursor:
                result = await cursor.fetchone()
                if result is None:
                    eembed = discord.Embed(title="Media Only Embed Settings", description="The media only channel warning embed is set to the default settings.", color=discord.Color.yellow())
                    eembed.set_footer(text="Use '/media embed' to set a custom embed message.")
                    eembed.set_thumbnail(url=self.bot.user.avatar.url)
                else:   
                    eembed = discord.Embed(title=result[0], description=result[1], color=color_map[result[2]])
                    if result[3]:
                        eembed.set_image(url=result[3])
                    if result[4]:
                        eembed.set_thumbnail(url=result[4])
                    if result[5]:
                        eembed.set_footer(text=result[5])
                await interaction.followup.send("This is your current warning embed", embed=eembed, ephemeral=True)

    @app_commands.command(name="auto_thread", description="Set the auto thread for media only channels")
    @app_commands.describe(action="Set auto thread to on or off")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.choices(
        action = [
            Choice(name="Set to on", value=1),
            Choice(name="Set to off", value=0)
        ]
    )
    async def set_auto_thread(self, interaction, action: Choice[int]) -> None:
        guild_id = interaction.guild_id
        async with aiosqlite.connect(modb) as db:
            async with db.execute('SELECT channel_id FROM media_only_channels WHERE guild_id = ?', (guild_id,)) as cursor:
                result = await cursor.fetchone()
                if not result:
                    embed = discord.Embed(title="No media only channels set up", description="Please set a media only channel before enabling auto threads.", color=discord.Color.red())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                else:
                    if action.value == 1 and result[0] == 0:
                        await db.execute("INSERT OR REPLACE INTO threads (guild_id, enabled) VALUES (?, ?)", (guild_id, action.value))
                        await db.commit()
                        embed = discord.Embed(title="Auto Threads Enabled", description="Auto threads have been enabled.", color=discord.Color.green())
                    elif action.value == 0 and result[0] == 1:
                        await db.execute("UPDATE threads SET enabled = ? WHERE guild_id = ?", (action.value, guild_id))
                        await db.commit()
                        embed = discord.Embed(title="Auto Threads Disabled", description="Auto threads have been disabled.", color=discord.Color.green())
                    elif action.value == 1 and result[0] == 1:
                        embed = discord.Embed(title="Auto Threads Already Enabled", description="Auto threads are already enabled.", color=discord.Color.yellow())
                    elif action.value == 0 and result[0] == 0:
                        embed = discord.Embed(title="Auto Threads Already Disabled", description="Auto threads are already disabled.", color=discord.Color.yellow())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                        
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        async with aiosqlite.connect(modb) as db:
            await db.execute("INSERT OR REPLACE INTO threads (guild_id, enabled) VALUES (?, ?)", (guild.id, 0))
            await db.commit()

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if message.author.bot:
            return
        async with aiosqlite.connect(modb) as db:
            async with db.execute('SELECT channel_id FROM media_only_channels WHERE guild_id = ?', (message.guild.id,)) as cursor:
                result = await cursor.fetchall()
            async with db.execute('SELECT enabled FROM threads WHERE guild_id = ?', (message.guild.id,)) as cursor:
                result2 = await cursor.fetchone()
                if message.channel.id in [channel[0] for channel in result]:
                    has_attachment = bool(message.attachments)
                    has_url = any(url.startswith("http") for url in re.findall(r'\bhttps?://\S+', message.content))
                    if not has_attachment and not has_url:
                        await message.delete()
                        async with aiosqlite.connect(moedb) as db:
                            async with db.execute('SELECT embed_title, embed_description, embed_color, embed_image, embed_thumbnail, embed_footer FROM MO_embed WHERE guild_id = ?', (message.guild.id,)) as cursor:
                                result = await cursor.fetchone()
                        if result:
                            embed = discord.Embed(title=result[0], description=result[1], color=color_map[result[2]])
                            if result[3]:
                                embed.set_image(url=result[3])
                            if result[4]:
                                embed.set_thumbnail(url=result[4])
                            if result[5]:
                                embed.set_footer(text=result[5])
                        if result is None:
                            if result2[0] == 0:
                                embed = discord.Embed(title="Media Only", description="Messages in this channel must contain media (pictures, videos, or links)! Please start a thread on the post you would like to comment on to leave comments.", color=discord.Color.red())
                            else:
                                embed = discord.Embed(title="Media Only", description="Messages in this channel must contain media (pictures, videos, or links)! Please post comments in the thread for the related post.", color=discord.Color.red())
                        await message.channel.send(embed=embed, delete_after=13)
                    elif result2[0] == 1:
                        thread = await message.create_thread(name="Discussion Thread")
                        await thread.send("This is the start of the thread discussion!")

class EmbedBuilder(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        

    async def build_embed(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(moedb) as db:
            async with db.execute('SELECT embed_title, embed_description, embed_color, embed_image, embed_thumbnail, embed_footer FROM MO_embed WHERE guild_id = ?', (interaction.guild.id,)) as cursor:
                result = await cursor.fetchone()
                if result[0] == None:
                    title = "This is the title"
                else:
                    title = result[0]
                if result[1] == None:
                    description = "This is the description"
                else:
                    description = result[1]
                if result[2] == None:
                    color = discord.Color.red()
                else:
                    color = color_map[result[2]]
        embed = discord.Embed(title=title, description=description, color=color)
        if result[3] != None:
            embed.set_image(url=result[3])
        else:
            embed.set_image(url=interaction.guild.icon.url)
        if result[4] != None:
            embed.set_thumbnail(url=result[4])
        else:
            embed.set_thumbnail(url=interaction.guild.me.avatar.url)
        if result[5] != None:
            embed.set_footer(text=result[5])
        else:
            embed.set_footer(text="This is the footer")
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Edit Title", custom_id="mo_edit_title", style=discord.ButtonStyle.primary, emoji="📝")
    async def edit_title(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(mo_edit_title())

    @discord.ui.button(label="Edit Description", style=discord.ButtonStyle.primary, emoji="📝")
    async def edit_description(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(mo_edit_description())

    @discord.ui.button(label="Edit Color", style=discord.ButtonStyle.primary, emoji="🎨")
    async def edit_color(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(title="Edit Color", description="Select the color you would like to use for the embed.", color=discord.Color.green())
        view = mo_edit_color()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Edit Footer", style=discord.ButtonStyle.primary, emoji="📝")
    async def edit_footer(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(mo_edit_footer())

    @discord.ui.button(label="Edit Image", style=discord.ButtonStyle.primary, emoji="🖼️")
    async def edit_image(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(mo_edit_image())

    @discord.ui.button(label="Edit Thumbnail", style=discord.ButtonStyle.primary, emoji="🖼️")
    async def edit_thumbnail(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(mo_edit_thumbnail())

    @discord.ui.button(label="Done", style=discord.ButtonStyle.green, emoji="✅")
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        async with aiosqlite.connect(moedb) as db:
            async with db.execute('SELECT embed_title, embed_description, embed_color, embed_image, embed_thumbnail, embed_footer FROM MO_embed WHERE guild_id = ?', (interaction.guild.id,)) as cursor:
                result = await cursor.fetchone()
        eembed = discord.Embed(title=result[0], description=result[1], color=color_map[result[2]])
        if result[3]:
            eembed.set_image(url=result[3])
        if result[4]:
            eembed.set_thumbnail(url=result[4])
        if result[5]:
            eembed.set_footer(text=result[5])
        view = embed_confirm()
        await interaction.response.edit_message(embed=eembed, view=view)

class embed_confirm(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(title="Media Only Embed Settings", description="Your media only channel warning embed settings have been saved.", color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        async with aiosqlite.connect(moedb) as db:
            async with db.execute('SELECT embed_title, embed_description, embed_color, embed_image, embed_thumbnail, embed_footer FROM MO_embed WHERE guild_id = ?', (interaction.guild.id,)) as cursor:
                result = await cursor.fetchone()
        eembed = discord.Embed(title=result[0], description=result[1], color=color_map[result[2]])
        if result[3]:
            eembed.set_image(url=result[3])
        if result[4]:
            eembed.set_thumbnail(url=result[4])
        if result[5]:
            eembed.set_footer(text=result[5])
        view = EmbedBuilder()
        await interaction.response.edit_message(embed=eembed, view=view)
        

class mo_edit_title(discord.ui.Modal, title="Edit Title"):
    def __init__(self) -> None:
        super().__init__()
        
    embed_title = discord.ui.TextInput(label="Title", placeholder="Enter the title", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(moedb) as db:
            await db.execute("UPDATE MO_embed SET embed_title = ? WHERE guild_id = ?", (self.embed_title.value, interaction.guild_id))
            await db.commit()
        await EmbedBuilder().build_embed(interaction)

class mo_edit_description(discord.ui.Modal, title="Edit Description"):
    def __init__(self) -> None:
        super().__init__()
        
    description = discord.ui.TextInput(label="Description", placeholder="Enter the description", style=discord.TextStyle.long)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(moedb) as db:
            await db.execute("UPDATE MO_embed SET embed_description = ? WHERE guild_id = ?", (self.description.value, interaction.guild_id))
            await db.commit()
        await EmbedBuilder().build_embed(interaction)

class mo_edit_color(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        color = color_drowpdown()
        self.add_item(color)

class color_drowpdown(discord.ui.Select):
    def __init__(self) -> None:
        super().__init__(placeholder="Select a color", options=[discord.SelectOption(label="Blue", value="discord.Color.blue()"), discord.SelectOption(label="Dark Blue", value="discord.Color.dark_blue()"), discord.SelectOption(label="Blurple", value="discord.Color.blurple()"), discord.SelectOption(label="Dark Gold", value="discord.Color.dark_gold()"), discord.SelectOption(label="Gold", value="discord.Color.gold()"), discord.SelectOption(label="Dark Gray", value="discord.Color.dark_gray()"), discord.SelectOption(label="Gray", value="discord.Color.gray()"), discord.SelectOption(label="Darker Gray", value="discord.Color.darker_gray()"), discord.SelectOption(label="Light Gray", value="discord.Color.light_gray()"), discord.SelectOption(label="Green", value="discord.Color.green()"), discord.SelectOption(label="Dark Green", value="discord.Color.dark_green()"), discord.SelectOption(label="Teal", value="discord.Color.teal()"), discord.SelectOption(label="Dark Teal", value="discord.Color.dark_teal()"),discord.SelectOption(label="Dark Magenta", value="discord.Color.dark_magenta()"), discord.SelectOption(label="Purple", value="discord.Color.purple()"), discord.SelectOption(label="Dark Purple", value="discord.Color.dark_purple()"), discord.SelectOption(label="Magenta", value="discord.Color.magenta()"), discord.SelectOption(label="Red", value="discord.Color.red()"), discord.SelectOption(label="Dark Red", value="discord.Color.dark_red()"), discord.SelectOption(label="Orange", value="discord.Color.orange()"), discord.SelectOption(label="Dark Orange", value="discord.Color.dark_orange()"), discord.SelectOption(label="Yellow", value="discord.Color.yellow()"), discord.SelectOption(label="Pink", value="discord.Color.pink()")])

    async def callback(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(moedb) as db:
            await db.execute("UPDATE MO_embed SET embed_color = ? WHERE guild_id = ?", (self.values[0], interaction.guild_id))
            await db.commit()
        await EmbedBuilder().build_embed(interaction)

class mo_edit_footer(discord.ui.Modal, title="Edit Footer"):
    def __init__(self) -> None:
        super().__init__()
        
    footer = discord.ui.TextInput(label="Footer", placeholder="Enter the footer", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(moedb) as db:
            await db.execute("UPDATE MO_embed SET embed_footer = ? WHERE guild_id = ?", (self.footer.value, interaction.guild_id))
            await db.commit()
        await EmbedBuilder().build_embed(interaction)

class mo_edit_image(discord.ui.Modal, title="Edit Image"):
    def __init__(self) -> None:
        super().__init__()
        
    image = discord.ui.TextInput(label="Image", placeholder="Enter the image URL", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.image.value.startswith("http"):
            async with aiosqlite.connect(moedb) as db:
                await db.execute("UPDATE MO_embed SET embed_image = ? WHERE guild_id = ?", (self.image.value, interaction.guild_id))
                await db.commit()
            await EmbedBuilder().build_embed(interaction)
        else:
            embed = discord.Embed(title="Invalid URL", description="Please enter a valid URL.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

class mo_edit_thumbnail(discord.ui.Modal, title="Edit Thumbnail"):
    def __init__(self) -> None:
        super().__init__()
        
    thumbnail = discord.ui.TextInput(label="Thumbnail", placeholder="Enter the thumbnail URL", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.thumbnail.value.startswith("http"):
            async with aiosqlite.connect(moedb) as db:
                await db.execute("UPDATE MO_embed SET embed_thumbnail = ? WHERE guild_id = ?", (self.thumbnail.value, interaction.guild_id))
                await db.commit()
            await EmbedBuilder().build_embed(interaction)
        else:
            embed = discord.Embed(title="Invalid URL", description="Please enter a valid URL.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot) -> None:
    await bot.add_cog(MediaOnlyCog(bot))