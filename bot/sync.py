import os
import discord
from discord.app_commands.commands import guilds
from discord.ext import commands
from discord import app_commands
import random
import asyncio

allowed_guilds = [1293647067998326936, 1262457887930716290]

class SyncCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.tree_on_error

    async def cog_unload(self) -> None:
        tree = self.bot.tree
        tree.on_error = self._old_tree_error

    async def tree_on_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_after = int(error.retry_after)
            if retry_after <= 60:
                retry_after1 = f"{retry_after} seconds"
            elif retry_after <= 3600:
                retry_after1 = f"{retry_after // 60} minutes"
            else:
                retry_after1 = f"{retry_after // 3600} hours"
            if interaction.command.name == "daily":
                embed = discord.Embed(
                    title="Daily",
                    description=f"You have already claimed your daily reward. Please try again in {retry_after1}.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            embed = discord.Embed(
                title="Command Cooldown",
                description=f"This command is on cooldown. Please try again in {retry_after1}.",
                color=discord.Color.red()
            )
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            except discord.HTTPException:
                print(f"Failed to send cooldown message for {interaction.user.name}#{interaction.user.discriminator}")

    @commands.command(name='sync', description='Syncs the bot', hidden=True)
    @commands.is_owner()
    async def sync(self, ctx) -> None:
        synced = await self.bot.tree.sync(guild=None)
        print(f'Synced {len(synced)} commands')
        all_commands = [cmd.name for cmd in self.bot.tree.get_commands()]
        print(f'Synced commands: {all_commands}')
        mod_group = discord.utils.get(self.bot.tree.get_commands(), name='mod')
        admin_group = discord.utils.get(self.bot.tree.get_commands(), name='admin')
        spotify_group = discord.utils.get(self.bot.tree.get_commands(), name='spotify')
        utility_group = discord.utils.get(self.bot.tree.get_commands(), name='utility')
        welcomer = discord.utils.get(self.bot.tree.get_commands(), name='welcomer')
        join_to_create = discord.utils.get(self.bot.tree.get_commands(), name='join_to_create')
        media_only = discord.utils.get(self.bot.tree.get_commands(), name='media_only')
        fun_group = discord.utils.get(self.bot.tree.get_commands(), name='fun')
        count = discord.utils.get(self.bot.tree.get_commands(), name='count')
        reddit_group = discord.utils.get(self.bot.tree.get_commands(), name='reddit')
        economy_group = discord.utils.get(self.bot.tree.get_commands(), name='economy')
        if mod_group:
            mod_commands = [cmd.name for cmd in mod_group.commands]
            print(f'Synced mod commands: {mod_commands}')
        else:
            print('Mod group not found')
        if admin_group:
            admin_commands = [cmd.name for cmd in admin_group.commands]
            print(f'Synced admin commands: {admin_commands}')
        else:
            print('Admin group not found')
        if spotify_group:
            spotify_commands = [cmd.name for cmd in spotify_group.commands]
            print(f'Synced spotify commands: {spotify_commands}')
        else:
            print('Spotify group not found')
        if utility_group:
            utility_commands = [cmd.name for cmd in utility_group.commands]
            print(f'Synced utility commands: {utility_commands}')
        else:
            print('Utility group not found')
        if welcomer:
            welcomer_commands = [cmd.name for cmd in welcomer.commands]
            print(f'Synced welcomer commands: {welcomer_commands}')
        else:
            print('Welcomer group not found')
        if join_to_create:
            join_to_create_commands = [cmd.name for cmd in join_to_create.commands]
            print(f'Synced join to create commands: {join_to_create_commands}')
        else:
            print('Join to create group not found')
        if media_only:
            media_only_commands = [cmd.name for cmd in media_only.commands]
            print(f'Synced media only commands: {media_only_commands}')
        else:
            print('Media only group not found')
        if fun_group:
            fun_commands = [cmd.name for cmd in fun_group.commands]
            print(f'Synced fun commands: {fun_commands}')
        else:
            print('Fun group not found')
        if count:
            count_commands = [cmd.name for cmd in count.commands]
            print(f'Synced count commands: {count_commands}')
        else:
            print('Count group not found')
        if reddit_group:
            reddit_commands = [cmd.name for cmd in reddit_group.commands]
            print(f'Synced reddit commands: {reddit_commands}')
        else:
            print('Reddit group not found')
        if economy_group:
            economy_commands = [cmd.name for cmd in economy_group.commands]
            print(f'Synced economy commands: {economy_commands}')
        else:
            print('Economy group not found')
        embed = discord.Embed(title='Sync Complete', description='The bot has been synced successfully.', color=discord.Color.green())
        embed.add_field(name='**SYNCED COMMANDS**', value=f"Synced {len(synced)} command groups")
        embed.add_field(name='**GROUPS SYNCED**', value=f"Synced commands: {', '.join(all_commands)}")
        if mod_group:
            embed.add_field(name=f"{len(mod_commands)} MODERATION COMMANDS SYNCED", value=f"Synced commands: {', '.join(mod_commands)}")
        if admin_group:
            embed.add_field(name=f"{len(admin_commands)} ADMIN COMMANDS SYNCED", value=f"Synced commands: {', '.join(admin_commands)}")
        if spotify_group:
            embed.add_field(name=f"{len(spotify_commands)} SPOTIFY COMMANDS SYNCED", value=f"Synced commands: {', '.join(spotify_commands)}")
        if utility_group:
            embed.add_field(name=f"{len(utility_commands)} UTILITY COMMANDS SYNCED", value=f"Synced commands: {', '.join(utility_commands)}")
        if welcomer:
            embed.add_field(name=f"{len(welcomer_commands)} WELCOMER COMMANDS SYNCED", value=f"Synced commands: {', '.join(welcomer_commands)}")
        if join_to_create:
            embed.add_field(name=f"{len(join_to_create_commands)} JOIN TO CREATE COMMANDS SYNCED", value=f"Synced commands: {', '.join(join_to_create_commands)}")
        if media_only:
            embed.add_field(name=f"{len(media_only_commands)} MEDIA ONLY COMMANDS SYNCED", value=f"Synced commands: {', '.join(media_only_commands)}")
        if fun_group:
            embed.add_field(name=f"{len(fun_commands)} FUN COMMANDS SYNCED", value=f"Synced commands: {', '.join(fun_commands)}")
        if count:
            embed.add_field(name=f"{len(count_commands)} COUNT COMMANDS SYNCED", value=f"Synced commands: {', '.join(count_commands)}")
        if reddit_group:
            embed.add_field(name=f"{len(reddit_commands)} REDDIT COMMANDS SYNCED", value=f"Synced commands: {', '.join(reddit_commands)}")
        if economy_group:
            embed.add_field(name=f"{len(economy_commands)} ECONOMY COMMANDS SYNCED", value=f"Synced commands: {', '.join(economy_commands)}")
        await ctx.send(embed=embed)
            
    @commands.command(name='syncg', description='Syncs the bot', hidden=True)
    @commands.is_owner()
    async def syncg(self, ctx, guild: discord.Guild) -> None:
        synced = await self.bot.tree.sync(guild=guild)
        print(f'Synced {len(synced)} commands')
        all_commands = [cmd.name for cmd in self.bot.tree.get_commands()]
        print(f'Synced commands: {all_commands}')
        embed = discord.Embed(title='Sync Complete', description='The bot has been synced successfully.', color=discord.Color.green())
        embed.add_field(name='**SYNCED COMMANDS**', value=f"Synced {len(synced)} command groups")
        embed.add_field(name='*GROUPS SYNCED*', value=f"Synced commands: {all_commands}")
        await ctx.send(embed=embed)

    @commands.command(name='clear', description='Clears all commands from the tree', hidden=True)
    @commands.is_owner()
    async def clear(self, ctx) -> None:
        ctx.bot.tree.clear_commands(guild=None)
        await ctx.send('Commands cleared.')

    async def cycle(self):
        while True:
            presences = [
                discord.Activity(type=discord.ActivityType.listening, name="your commands"),
                discord.Activity(type=discord.ActivityType.watching, name="your messages"),
                discord.Activity(type=discord.ActivityType.listening, name=f"to {len(self.bot.guilds)} servers"),
                discord.Activity(type=discord.ActivityType.listening, name="your messages"),
                discord.Activity(type=discord.ActivityType.watching, name=f"over {len(self.bot.guilds)} servers"),
                discord.Activity(type=discord.ActivityType.listening, name="your messages"),
                discord.Activity(type=discord.ActivityType.watching, name=f"over {len(self.bot.users)} users"),
                discord.Activity(type=discord.ActivityType.listening, name=f"{len(self.bot.users)} users")
            ]
            Statuses = [discord.Status.online, discord.Status.idle, discord.Status.do_not_disturb]
            Activity= random.choice(presences)
            Status = random.choice(Statuses)
            await self.bot.change_presence(activity=Activity, status=Status)
            print(f'Changed status to {Activity} {Status}')
            await asyncio.sleep(3600)
            
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print(f'Logged in as {self.bot.user.name} (ID: {self.bot.user.id})')
        self.bot.loop.create_task(self.cycle())

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.guild.id not in allowed_guilds and isinstance(error, commands.NotOwner):
            print(f"Error: this user tried to use an owner command in another guild {ctx.author.name} in {ctx.guild.name}:{ctx.guild.id}")
            return
        if ctx.guild.id not in allowed_guilds:
            print(f"Error: this user tried to use a command in another guild {ctx.author.name} in {ctx.guild.name}:{ctx.guild.id}")
            return
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Invalid command. Type `!wchelp` for a list of available commands.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have the required permissions to use this command.")
        elif isinstance(error, commands.NotOwner):
            print(f"Error: this user tried to use an owner command {ctx.author.name}")
            await ctx.send("You cannot use this command because you are not the owner of this bot.")
        
async def setup(bot) -> None:
    await bot.add_cog(SyncCog(bot))