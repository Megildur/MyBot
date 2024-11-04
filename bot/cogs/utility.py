import discord
from discord import app_commands
from discord.ext import commands
import deep_translator
from deep_translator import GoogleTranslator, single_detection
import langcodes

class Utility(commands.GroupCog, name="utility"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="Translate to English",
            callback=self.Translate_to_English,
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_load(self):
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
    ):
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

    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.checks.cooldown(2, 20, key=lambda i: (i.guild_id, i.user.id))
    async def Translate_to_English(self, interaction: discord.Interaction, message: discord.Message) -> None:
        try:
            translator = GoogleTranslator(source='auto', target='en')
            translation = translator.translate(message.content)
            source_language = single_detection(message.content, api_key='9749cb5e503e0646c3c86dec50cdfabe')
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
        await interaction.response.send_message(f"Pong! Latency: {latency}ms")

async def setup(bot) -> None:
    await bot.add_cog(Utility(bot))