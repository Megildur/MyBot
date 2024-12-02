import discord
from discord.ext import commands
from discord import app_commands
import os
import easy_pil
import random
import aiosqlite
from bot.utils.mod_helpers import bot_can_moderate_roles
from discord import ChannelType
from discord.app_commands import AppCommandChannel, AppCommandThread
from discord.ui import ChannelSelect, RoleSelect
from bot.utils.paginator import ButtonPaginator

welcomer = "data/welcomer.db"

@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
class Welcomer(commands.GroupCog, name="welcomer"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        async with aiosqlite.connect(welcomer) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS wlcmer (guild_id INTEGER, channel_id INTEGER, message TEXT, image INTEGER, role_id INTEGER, color TEXT, PRIMARY KEY (guild_id))"
            )
            await db.commit()
            
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        async with aiosqlite.connect(welcomer) as db:
            await db.execute(
                "INSERT OR REPLACE INTO wlcmer (guild_id, channel_id, message, image, role_id, color) VALUES (?, ?, ?, ?, ?, ?)",
                (guild.id, 0, 0, 0, 0, "white"),
            )
            await db.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        async with aiosqlite.connect(welcomer) as db:
            cursor = await db.execute("SELECT channel_id, message, image, role_id, color FROM wlcmer WHERE guild_id = ?", (member.guild.id,))
            data = await cursor.fetchone()
        if data[3] != 0:
            role = member.guild.get_role(data[3])
            await member.add_roles(role)
        welcome_channel = self.bot.get_channel(data[0])
        if welcome_channel == 0:
            return
        if data[2] == 0:
            images = [image for image in os.listdir("./data/images/default")]
        if data[2] != 0:
            images = [image for image in os.listdir(f"./data/images/{member.guild.id}/")]
        random_image = random.choice(images)
        if data[2] == 0:
            bg = easy_pil.Editor(f'./data/images/default/{random_image}').resize((1920, 1080))
        else:
            bg = easy_pil.Editor(f'./data/images/{member.guild.id}/{random_image}').resize((1920, 1080))
        avatar_image = await easy_pil.load_image_async(str(member.avatar.url))
        avatar = easy_pil.Editor(avatar_image).resize((250, 250)).circle_image()

        big_font = easy_pil.Font.poppins(size=90, variant="bold")
        small_font = easy_pil.Font.poppins(size=60, variant="regular")

        bg.paste(avatar, (835, 340))
        bg.ellipse((835, 340), 250, 250, outline=data[4], stroke_width=5)
        bg.text((960, 620), f"Welcome to {member.guild.name}", font=big_font, color=data[4], align="center")
        bg.text((960, 740), f"{member.name} is member #{member.guild.member_count}!", font=small_font, color=data[4], align="center")
        img_file = discord.File(fp=bg.image_bytes, filename=random_image)
        if data[1] == "0":
            await welcome_channel.send(f"Welcome {member.mention}! Please make sure to read the rules! Thankyou for joining our server!", file=img_file)
        else:
            await welcome_channel.send(data[1].format(_mention=member.mention, _name=member.name), file=img_file)

    @app_commands.command(name="setup", description="Setup the welcomer")
    @app_commands.default_permissions(manage_guild=True)
    async def welcomer_setup(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(welcomer) as db:
            cursor = await db.execute("SELECT channel_id, role_id, message, image, color FROM wlcmer WHERE guild_id = ?", (interaction.guild_id,))
            row = await cursor.fetchone()
            if row is None:
                embed = discord.Embed(title="Welcome Settings", description="No settings found", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            channel_id = row[0]
            role_id = row[1]
            message = row[2]
            image = row[3]
            color = row[4]
            if channel_id == 0:
                channel_name = "Not Set"
            else:
                channel = interaction.guild.get_channel(channel_id)
                if channel is None:
                    channel_name = "Not Set"
                else:
                    channel_name = channel.mention
            if role_id == "0":
                role_name = "Not Set"
            else:
                role = interaction.guild.get_role(role_id)
                if role is None:
                    role_name = "Not Set"
                else:
                    role_name = role.mention
            if message == "0":
                message_text = "Not Set"
            else:
                message_text = message
            if image == 0:
                image = "Default"
            else:
                image = "Custom"
            if color == "0":
                color_text = "white"
            else:
                color_text = color
            embed = discord.Embed(title="Welcome Settings", description=f"Channel: {channel_name}\nAuto-Role: {role_name}\nWelcome Message: {message_text}\nWecome Card Image: {image}\nImage Text Color: {color_text}", color=discord.Color.green())
            embed.set_thumbnail(url=interaction.guild.icon.url)
            embed.add_field(name="Please use the buttons below to change the settings.", value="Make sure you set a channel to make sure the welcomer is enabled")
            embed.set_footer(text="Please use '/welcomer image_add' to upload custom welcome images or '/welcomer image_remove' to remove an image. You can set more than one image and they will be chosen from randomly")
            await interaction.response.send_message(embed=embed, ephemeral=True, view=WelcomerView(self.bot))

    async def welcomer_embed(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(welcomer) as db:
            cursor = await db.execute("SELECT channel_id, role_id, message, image, color FROM wlcmer WHERE guild_id = ?", (interaction.guild_id,))
            row = await cursor.fetchone()
            if row is None:
                embed = discord.Embed(title="Welcome Settings", description="No settings found", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            channel_id = row[0]
            role_id = row[1]
            message = row[2]
            image = row[3]
            color = row[4]
            if channel_id == 0:
                channel_name = "Not Set"
            else:
                channel = interaction.guild.get_channel(channel_id)
                if channel is None:
                    channel_name = "Not Set"
                else:
                    channel_name = channel.mention
            if role_id == "0":
                role_name = "Not Set"
            else:
                role = interaction.guild.get_role(role_id)
                if role is None:
                    role_name = "Not Set"
                else:
                    role_name = role.mention
            if message == "0":
                message_text = "Not Set"
            else:
                message_text = message
            if image == 0:
                image = "Default"
            else:
                image = "Custom"
            if color == "0":
                color_text = "white"
            else:
                color_text = color
            embed = discord.Embed(title="Welcome Settings", description=f"Channel: {channel_name}\nAuto-Role: {role_name}\nWelcome Message: {message_text}\nWecome Card Image: {image}\nImage Text Color: {color_text}", color=discord.Color.green())
            embed.set_thumbnail(url=interaction.guild.icon.url)
            embed.add_field(name="Please use the buttons below to change the settings.", value="Make sure you set a channel to make sure the welcomer is enabled")
            embed.set_footer(text="Please use '/welcomer image_add' to upload custom welcome images or '/welcomer image_remove' to remove an image. You can set more than one image and they will be chosen from randomly")
            await interaction.response.edit_message(embed=embed, view=WelcomerView(self.bot))

    @app_commands.command(name="image_add", description="Add custom welcome image")
    @app_commands.describe(image="Image to add")
    @app_commands.default_permissions(manage_guild=True)
    async def add_custom_welcome_image(self, interaction: discord.Interaction, image: discord.Attachment):
        await interaction.response.defer(ephemeral=True, thinking=True)
        if not image.filename.endswith((".png", ".jpg", ".jpeg")):
            embed = discord.Embed(title="Custom Welcome Image", description="Only PNG, JPG and JPEG images are allowed", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        if image.size > 5000000:
            embed = discord.Embed(title="Custom Welcome Image", description="Image size must be less than 5MB", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        image_directory = f"./data/images/{interaction.guild_id}"
        os.makedirs(image_directory, exist_ok=True)
        image_path = os.path.join(image_directory, image.filename)
        await image.save(image_path)
        file = discord.File(image_path, filename=image.filename)
        embed = discord.Embed(
            title="Custom Welcome Image",
            description="Image successfully saved and displayed below!",
            color=discord.Color.green()
        )
        embed.set_image(url=f"attachment://{image.filename}")
        async with aiosqlite.connect(welcomer) as db:
            await db.execute("UPDATE wlcmer SET image = ? WHERE guild_id = ?", (1, interaction.guild_id))
            await db.commit()
            await interaction.followup.send(embed=embed, ephemeral=True, file=file)

    @app_commands.command(name="image_remove", description="Remove custom welcome image")
    @app_commands.default_permissions(manage_guild=True)
    async def remove_custom_welcome_image(self, interaction: discord.Interaction):
        images = [image for image in os.listdir(f"./data/images/{interaction.guild_id}")]
        if not images:
            embed = discord.Embed(title="Custom Welcome Image", description="No custom welcome image found", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        async with aiosqlite.connect(welcomer) as db:
            await db.execute("UPDATE wlcmer SET image = ? WHERE guild_id = ?", (0, interaction.guild_id))
            await db.commit()
        for image in images:
            os.remove(f"./data/images/{interaction.guild_id}/{image}")
            embed = discord.Embed(title="Custom Welcome Image", description="Custom welcome images removed", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="current_settings", description="View current settings")
    @app_commands.default_permissions(manage_guild=True)
    async def current_settings(self, interaction: discord.Interaction):
        async with aiosqlite.connect(welcomer) as db:
            cursor = await db.execute("SELECT channel_id, role_id, message, image, color FROM wlcmer WHERE guild_id = ?", (interaction.guild_id,))
            row = await cursor.fetchone()
            if row is None:
                embed = discord.Embed(title="Welcome Settings", description="No settings found", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            channel_id = row[0]
            role_id = row[1]
            message = row[2]
            image = row[3]
            color = row[4]
            if channel_id == 0:
                channel_name = "Not Set"
            else:
                channel = interaction.guild.get_channel(channel_id)
                if channel is None:
                    channel_name = "Not Set"
                else:
                    channel_name = channel.mention
            if role_id == "0":
                role_name = "Not Set"
            else:
                role = interaction.guild.get_role(role_id)
                if role is None:
                    role_name = "Not Set"
                else:
                    role_name = role.mention
            if message == "0":
                message_text = "Not Set"
            else:
                message_text = message
            if image == 0:
                image = "Default"
            else:
                image = "Custom"
            if color == "0":
                color_text = "white"
            else:
                color_text = color
            embed = discord.Embed(title="Welcome Settings", description=f"Channel: {channel_name}\nAuto-Role: {role_name}\nWelcome Message: {message_text}\nWecome Card Image: {image}\nImage Text Color: {color_text}", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)

class WelcomerView(discord.ui.View):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Change Channel", style=discord.ButtonStyle.blurple, custom_id="welcomer_channel", row=0, emoji="📝")
    async def welcomer_channel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(title="Welcomer Channel", description="Please select the channel you want to set as the welcomer channel.", color=discord.Color.green())
        embed.set_thumbnail(url=interaction.guild.icon.url)
        await interaction.response.edit_message(embed=embed, view=WelcomerChannel(self.bot))

    @discord.ui.button(label="Disable Channel", style=discord.ButtonStyle.red, custom_id="welcomer_disable", row=0, emoji="🚫")
    async def welcomer_disable(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        async with aiosqlite.connect(welcomer) as db:
            async with db.execute("SELECT channel_id FROM wlcmer WHERE guild_id = ?", (interaction.guild_id,)) as cursor:
                data = await cursor.fetchone()
            if data[0] == 0:
                embed = discord.Embed(title="Welcome Channel Not Set", description="Welcomer is not enabled! Please set a welcome channel first!", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await db.execute("UPDATE wlcmer SET channel_id = ? WHERE guild_id = ?", (0, interaction.guild_id))
                await db.commit()
                await Welcomer(self.bot).welcomer_embed(interaction)

    @discord.ui.button(label="Change Auto-Role", style=discord.ButtonStyle.blurple, custom_id="welcomer_role", emoji="🎭", row=1)
    async def welcomer_role(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(title="Welcomer Role", description="Please select the role you want to set as the Autorole.", color=discord.Color.green())
        embed.set_thumbnail(url=interaction.guild.icon.url)
        await interaction.response.edit_message(embed=embed, view=WelcomerRole(self.bot))

    @discord.ui.button(label="Disable Auto-Role", style=discord.ButtonStyle.red, custom_id="welcomer_disable_role", emoji="🚫", row=1)
    async def autorole_disable(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        async with aiosqlite.connect(welcomer) as db:
            async with db.execute("SELECT role_id FROM wlcmer WHERE guild_id = ?", (interaction.guild_id,)) as cursor:
                data = await cursor.fetchone()
            if data[0] == 0:
                embed = discord.Embed(title="Auto Role Not Set", description="Auto role is not enabled! Please set a auto role first!", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await db.execute("UPDATE wlcmer SET role_id = ? WHERE guild_id = ?", (0, interaction.guild_id))
                await db.commit()
                await Welcomer(self.bot).welcomer_embed(interaction)

    @discord.ui.button(label="Change Custom Welcome Message", style=discord.ButtonStyle.blurple, custom_id="welcomer_message", emoji="📝", row=2)
    async def welcomer_message(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(WelcomerMessage(self.bot))

    @discord.ui.button(label="Disable Custom Welcome Message", style=discord.ButtonStyle.red, custom_id="welcomer_disable_message", emoji="🚫", row=2)
    async def welcomer_disable_message(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        async with aiosqlite.connect(welcomer) as db:
            async with db.execute("SELECT message FROM wlcmer WHERE guild_id = ?", (interaction.guild_id,)) as cursor:
                data = await cursor.fetchone()
            if data[0] == "0":
                embed = discord.Embed(title="Custom Welcome Message Not Set", description="Custom welcome message is not enabled! Please set a custom welcome message first!", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            await db.execute("UPDATE wlcmer SET message = ? WHERE guild_id = ?", (0, interaction.guild_id))
            await db.commit()
            await Welcomer(self.bot).welcomer_embed(interaction)

    @discord.ui.button(label="Change Custom Welcome Card Image Text Colors", style=discord.ButtonStyle.blurple, custom_id="welcomer_color", emoji="🎨", row=3)
    async def welcomer_color(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(WelcomerColor(self.bot))

    @discord.ui.button(label="Disable Custom Welcome Card Image Text Colors", style=discord.ButtonStyle.red, custom_id="welcomer_disable_color", emoji="🚫", row=3)
    async def welcomer_disable_color(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        async with aiosqlite.connect(welcomer) as db:
            async with db.execute("SELECT color FROM wlcmer WHERE guild_id = ?", (interaction.guild_id,)) as cursor:
                data = await cursor.fetchone()
            if data[0] == "0":
                embed = discord.Embed(title="Custom Welcome Card Image Text Colors Not Set", description="Custom welcome card image text colors are not enabled! Please set a custom welcome card image text colors first!", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            await db.execute("UPDATE wlcmer SET color = ? WHERE guild_id = ?", (0, interaction.guild_id))
            await db.commit()
            await Welcomer(self.bot).welcomer_embed(interaction)
        
class WelcomerChannel(discord.ui.View):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(cls=ChannelSelect, placeholder="Select a channel", custom_id="welcomer_channel_select", min_values=1, max_values=1, channel_types=[discord.ChannelType.text])
    async def welcomer_channel_select(self, interaction: discord.Interaction, select: list[AppCommandChannel]) -> None:
        channel = interaction.guild.get_channel(select.values[0].id)
        bot_permissions = channel.permissions_for(interaction.guild.me)
        if not bot_permissions.send_messages:
            embed = discord.Embed(title="Permission Error", description=f"I don't have permission to send messages in {channel.mention}. Please check my permissions.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        async with aiosqlite.connect(welcomer) as db:
            await db.execute("UPDATE wlcmer SET channel_id = ? WHERE guild_id = ?", (channel.id, interaction.guild_id))
            await db.commit()
            await Welcomer(self.bot).welcomer_embed(interaction)

class WelcomerRole(discord.ui.View):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(cls=RoleSelect, placeholder="Select a role", custom_id="welcomer_role_select", min_values=1, max_values=1)
    async def auto_role_set(self, interaction: discord.Interaction, select: RoleSelect) -> None:
        role = select.values[0]
        if not bot_can_moderate_roles(role):
            embed = discord.Embed(title="Auto Role Set", description=f"I don't have permission to assign {role.mention} to new members", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        async with aiosqlite.connect(welcomer) as db:
            await db.execute("UPDATE wlcmer SET role_id = ? WHERE guild_id = ?", (role.id, interaction.guild_id))
            await db.commit()
            await Welcomer(self.bot).welcomer_embed(interaction)

class WelcomerMessage(discord.ui.Modal):
    def __init__(self, bot) -> None:
        super().__init__(title="Custom Welcome Message" , timeout=None)
        self.bot = bot
    message = discord.ui.TextInput(label="Message", style=discord.TextStyle.long, placeholder="Enter the message you want to send", required=True, max_length=2000)
    async def on_submit(self, interaction: discord.Interaction) -> None:
        message = self.message.value
        async with aiosqlite.connect(welcomer) as db:
            await db.execute("UPDATE wlcmer SET message = ? WHERE guild_id = ?", (message, interaction.guild_id))
            await db.commit()
            await Welcomer(self.bot).welcomer_embed(interaction)

class WelcomerColor(discord.ui.Modal):
    def __init__(self, bot) -> None:
        super().__init__(title="Custom Image Text Colors", timeout=None)
        self.bot = bot

    color = discord.ui.TextInput(label="Color", style=discord.TextStyle.short, placeholder="Enter the color you want to use", required=True, max_length=7)
    async def on_submit(self, interaction: discord.Interaction) -> None:
        color = self.color.value
        if not color.startswith("#"):
            embed = discord.Embed(title="Image Text Color", description="Color must be in hex format", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if len(color) != 7:
            embed = discord.Embed(title="Image Text Color", description="Color must be in hex format", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        async with aiosqlite.connect(welcomer) as db:
            await db.execute("UPDATE wlcmer SET color = ? WHERE guild_id = ?", (color, interaction.guild_id))
            await db.commit()
            await Welcomer(self.bot).welcomer_embed(interaction)
                    
async def setup(bot):
    await bot.add_cog(Welcomer(bot))