import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from datetime import timedelta
from ..moderation import Moderation

reports = 'data/reports.db'

class ReportMessage(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="Report Message",
            callback=self.report_message_context
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_load(self) -> None:
        async with aiosqlite.connect(reports) as db:
            await db.execute('CREATE TABLE IF NOT EXISTS reports (guild_id INTEGER PRIMARY KEY, mod_report_channel INTEGER)')
            await db.commit()

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu)

    async def report_message_context(self, interaction: discord.Interaction, message: discord.Message) -> None:
        modal = ReportMessageModal(self.bot, message, message.author, message.channel)
        await interaction.response.send_modal(modal)

class ReportMessageModal(discord.ui.Modal):
    def __init__(self, bot, message, user, channel) -> None:
        self.bot = bot
        self.message = message
        self.user = user
        self.channel = channel
        super().__init__(title="Report a Message to Server Staff")
        self.user_input = discord.ui.TextInput(
            label=f"Report Message: {self.message.content}",
            style=discord.TextStyle.long,
            placeholder="Reason...",
            required=True,
        )
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)
        async with aiosqlite.connect(reports) as db:
            async with db.execute('SELECT mod_report_channel FROM reports WHERE guild_id = ?', (interaction.guild_id,)) as cursor:
                result = await cursor.fetchone()
                if result is None:
                    embed = discord.Embed(title="Report Channel Not Set", description="The report channel has not been set for this server. Please conttact server staff and have them set the report channel using the `/set_report_channel` command.", color=discord.Color.red())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                else:
                    mod_report_channel = result[0]
        embed = discord.Embed(title="Report Message", description=f'Reason: {self.user_input.value}', color=discord.Color.red())
        embed.set_footer(text=f'Reported by {interaction.user.name}#{interaction.user.discriminator}', icon_url=interaction.user.avatar.url)
        embed.timestamp = discord.utils.utcnow()
        embed.add_field(name="Message:", value=f'[Jump to Message]({self.message.jump_url})' if self.message else 'Message not found')
        embed.add_field(name="Message Content:", value=self.message.content if self.message else 'Message not found')
        embed.add_field(name="Reported User:", value=f'{self.user.mention} ({self.user.id})' if self.user else 'Message not found')
        embed.add_field(name="Channel:", value=self.channel.mention)
        await interaction.followup.send('This report has been sent to staff for review', embed=embed, ephemeral=True)
        view = ReportButtons(self.bot, self.user, self.message, self.channel, self.user_input.value)
        report_channel = self.bot.get_channel(mod_report_channel)
        await report_channel.send(embed=embed, view=view)


class ReportButtons(discord.ui.View):
    def __init__(self, bot, user, message, channel, input, timeout=None) -> None:
        self.bot = bot
        self.user = user
        self.message = message
        self.channel = channel
        self.input = input
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="mod_delete_button", emoji="🗑️")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled=True
        button.style=discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        await self.message.delete()

    @discord.ui.button(label="Timeout", style=discord.ButtonStyle.danger, custom_id="mod_timeout_button", emoji="🔇")
    async def mute_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled=True
        button.style=discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        embed = discord.Embed(title="Choose a Timeout Duration", description="Please select a timeout duration from the dropdown menu below.", color=discord.Color.red())
        await interaction.followup.send(embed=embed, view=TimeOutSelect(self.bot, self.user, self.input), ephemeral=True)

    @discord.ui.button(label="Warn", style=discord.ButtonStyle.danger, custom_id= "mod_warn_button", emoji="⚠️")
    async def warn_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled=True
        button.style=discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        embed = discord.Embed(title="Warning", description=f'Reason: {self.input}', color=discord.Color.red())
        embed.set_footer(text=f'Warned by {interaction.user.mention}#{interaction.user.discriminator}', icon_url=interaction.user.avatar.url)
        embed.timestamp = discord.utils.utcnow()
        embed.add_field(name="Message:", value=f'[Jump to Message]({self.message.jump_url})' if self.message else 'Message not found')
        embed.add_field(name="Message Content:", value=self.message.content if self.message else 'Message not found')
        await self.channel.send(f"{self.user.mention}", embed=embed)
        await Moderation(self.bot).send_mod_message(interaction, self.user, "warn", self.input)

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.danger, custom_id= "mod_ban_button", emoji="🔨")
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled=True
        button.style=discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        embed = discord.Embed(title="Choose a Ban Duration", description="Please select a ban duration from the dropdown menu below.", color=discord.Color.red())
        await interaction.followup.send(embed=embed, view=BanSelect(self.bot, self.user, input), ephemeral=True)

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.danger, custom_id= "mod_kick_button", emoji="🦶")
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        try:
            button.disabled=True
            button.style=discord.ButtonStyle.secondary
            await interaction.response.edit_message(view=self)
            await self.user.kick(reason=self.input)
            await Moderation(self.bot).send_mod_message(interaction, self.user, "kick", self.input)
        except Exception as e:
            await interaction.response.send_message(f"Failed to timeout {self.user.mention}. Error: {e}")
            
class TimeOutSelect(discord.ui.View):
    def __init__(self, bot, user, input, timeout=None) -> None:
        self.bot = bot
        self.user = user
        self.input = input
        super().__init__(timeout=timeout)
        Usertimeout = TODropdownMenu(self.bot, self.user, self.input)
        self.add_item(Usertimeout)

class TODropdownMenu(discord.ui.Select):
    def __init__(self, bot, user, input) -> None:
        self.bot = bot
        self.user = user
        self.input = input
        super().__init__(
            placeholder="Timeout Duration...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="30 Minutes", value="30"),
                discord.SelectOption(label="1 Hour", value="60"),
                discord.SelectOption(label="2 Hours", value="120"),
                discord.SelectOption(label="3 Hours", value="180"),
                discord.SelectOption(label="4 Hours", value="240"),
                discord.SelectOption(label="6 Hours", value="360"),
                discord.SelectOption(label="12 Hours", value="720"),
                discord.SelectOption(label="1 Day", value="3600"),
                discord.SelectOption(label="2 Days", value="7200"),
                discord.SelectOption(label="3 Days", value="10800"),
                discord.SelectOption(label="7 Days", value="25200"),
                discord.SelectOption(label="14 Days", value="50400"),
                discord.SelectOption(label="28 Days", value="100800")
            ]
        )
        
    async def callback(self, interaction: discord.Interaction) -> None:
        selected_value = int(self.values[0])
        try:
            timeout_duration = timedelta(minutes=selected_value)
            await self.user.timeout(timeout_duration)
            await Moderation(self.bot).send_mod_message(interaction, self.user, "Timeout", self.input)
        except Exception as e:
            await interaction.response.send_message(f"Failed to timeout {self.user.mention}. Error: {e}")

class BanSelect(discord.ui.View):
    def __init__(self, bot, user, input, timeout=None) -> None:
        self.bot = bot
        self.user = user
        self.input = input
        super().__init__(timeout=timeout)
        Userban = BanDropdownMenu(self.bot, self.user, self.input)
        self.add_item(Userban)

class BanDropdownMenu(discord.ui.Select):
    def __init__(self, bot, user, input) -> None:
        self.bot = bot
        self.user = user
        self.input = input
        super().__init__(
            placeholder="Ban Duration...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="30 Minutes", value="30"),
                discord.SelectOption(label="1 Hour", value="60"),
                discord.SelectOption(label="2 Hours", value="120"),
                discord.SelectOption(label="3 Hours", value="180"),
                discord.SelectOption(label="4 Hours", value="240"),
                discord.SelectOption(label="6 Hours", value="360"),
                discord.SelectOption(label="12 Hours", value="720"),
                discord.SelectOption(label="1 Day", value="3600"),
                discord.SelectOption(label="2 Days", value="7200"),
                discord.SelectOption(label="3 Days", value="10800"),
                discord.SelectOption(label="7 Days", value="25200"),
                discord.SelectOption(label="14 Days", value="50400"),
                discord.SelectOption(label="28 Days", value="100800"),
                discord.SelectOption(label="Forever", value="0")
            ])

    async def callback(self, interaction: discord.Interaction) -> None:
        selected_value = int(self.values[0])
        try:
            if selected_value == 0:
                await Moderation(self.bot).send_mod_message(interaction, self.user, "ban", self.input)
            else:
                await self.user.ban(reason=self.input)
                await Moderation(self.bot).save_temporary_action(self.user.id, interaction.guild_id, 'ban', selected_value)
                expiration = discord.utils.utcnow() + timedelta(minutes=selected_value)
                experation_time = int(expiration.timestamp())
                expiration_time_str = f"<t:{experation_time}:R>"
                await Moderation(self.bot).send_mod_message(interaction, self.user, "ban", self.input, expiration_time_str)
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban {self.user.mention}. Error: {e}")

async def setup(bot) -> None:
    await bot.add_cog(ReportMessage(bot))