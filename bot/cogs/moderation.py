import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
from typing import Optional, Literal, List
from bot.utils.mod_helpers import mod_build_embed, can_moderate, get_or_create_mute_role, bot_can_moderate, can_moderate_roles, bot_can_moderate_roles, parse_duration, check_bot_permissions, bot_has_permission
from bot.utils.paginator import ButtonPaginator
from bot.utils.moderation_log import moderation_log, moderation_log_fetch
from datetime import datetime, timedelta
import asyncio

persistent_data = "data/persistent_data.db"

class Moderation(commands.GroupCog, group_name="mod"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        await self.initialize_database()
        self.check_expired_actions.start()
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
            embed = discord.Embed(
                title="Command Cooldown",
                description=f"This command is on cooldown. Please try again in {retry_after} seconds.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            print(f"An error occurred: {error}")
            await interaction.followup.send(f"An error occurred: {error}", ephemeral=True)

    def access_log_channel_id(self, guild_id) -> Optional[int]:
        admin_cog = self.bot.admin_cog
        if admin_cog:
            return admin_cog.get_log_channel_id(guild_id)
        return None

    async def initialize_database(self) -> None:
        async with aiosqlite.connect(persistent_data) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS temporary_actions (
                    user_id INTEGER,
                    guild_id INTEGER,
                    action_type TEXT,
                    expires_at TIMESTAMP
                )
            """)
            await db.commit()

    @tasks.loop(seconds=60)
    async def check_expired_actions(self) -> None:
        while True:
            current_time = datetime.utcnow()
            async with aiosqlite.connect(persistent_data) as db:
                async with db.execute(
                    "SELECT user_id, guild_id, action_type FROM temporary_actions WHERE expires_at <= ?", (current_time,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    for row in rows:
                        user_id, guild_id, action_type = row
                        guild = self.bot.get_guild(guild_id)
                        if guild:
                            member = guild.get_member(user_id)
                            if action_type == 'mute' and member:
                                mute_role = discord.utils.get(guild.roles, name="Muted")
                                if mute_role and mute_role in member.roles:
                                    await member.remove_roles(mute_role)
                                    log_channel_id = self.access_log_channel_id(guild_id)
                                    if log_channel_id:
                                        log_channel = guild.get_channel(log_channel_id)
                                        if log_channel:
                                            embed = await mod_build_embed("Unmute", member, self.bot.user, f"Mute duration expired for user")
                                            await log_channel.send(embed=embed)
                                            await moderation_log(guild, member, "unmute", "Mute duration expired for user", self.bot.user)
                            elif action_type == 'ban':
                                user_unban = discord.Object(user_id)
                                user = await self.bot.fetch_user(user_id)
                                await guild.unban(user_unban)
                                log_channel_id = self.access_log_channel_id(guild_id)
                                if log_channel_id:
                                    log_channel = guild.get_channel(log_channel_id)
                                    if log_channel:
                                        embed = await mod_build_embed("Unban", user, self.bot.user, f"Ban duration expired for user")
                                        await log_channel.send(embed=embed)
                                        await moderation_log(guild, user, "unban", "Ban duration expired for user", self.bot.user)
                        await db.execute(
                            "DELETE FROM temporary_actions WHERE user_id = ? AND guild_id = ? AND action_type = ?",
                            (user_id, guild_id, action_type)
                        )
                        await db.commit()
        

    async def save_temporary_action(self, user_id, guild_id, action_type, duration_minutes) -> None:
        expiration_time = discord.utils.utcnow() + timedelta(minutes=duration_minutes)
        async with aiosqlite.connect(persistent_data) as db:
            await db.execute(
                "INSERT INTO temporary_actions (user_id, guild_id, action_type, expires_at) VALUES (?, ?, ?, ?)",
                (user_id, guild_id, action_type, expiration_time)
            )
            await db.commit()

    async def parse_temporary_action(self, user_id, guild_id, action_type, duration) -> Optional[int]:
        duration_str = duration
        duration_minutes = parse_duration(duration_str)
        if duration_minutes:
            await self.save_temporary_action(user_id, guild_id, action_type, duration_minutes)
            return duration_minutes

    async def send_mod_message(self, interaction, member: discord.Member, action_type: str, reason: str, duration: Optional[str] = None) -> None:
        if duration is None:
            embed = await mod_build_embed(action_type, member, interaction.user, reason)
        else:
            embed = await mod_build_embed(action_type, member, interaction.user, reason, duration)
        await interaction.followup.send(embed=embed)
        log_channel_id = self.access_log_channel_id(interaction.guild_id)
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)
        await moderation_log(interaction.guild, member, action_type, reason, interaction.user, duration)

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(member="The member to kick", reason="The reason for kicking the member")
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.user.id))
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided.") -> None:
        try:
            await interaction.response.defer()
            if not await bot_has_permission(interaction, "kick_members"):
                await interaction.followup.send("I don't have permission to kick members.", ephemeral=True)
                return
            if can_moderate(interaction.user, member):
                await member.kick(reason=reason)
                await self.send_mod_message(interaction, member, "Kick", reason)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to kick this member.", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to kick this member.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.NotFound:
            embed = discord.Embed(title="Error", description="This member was not found.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to kick this member.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(member="The member to ban", reason="The reason for banning the member", duration="The duration of the ban (e.g., 1d, 2h, 30m)")
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.user.id))
    async def ban(self, interaction: discord.Interaction, member: discord.Member, duration: Optional[str] = None, reason: str = "No reason provided.") -> None:
        try:
            await interaction.response.defer()
            if not await bot_has_permission(interaction, "ban_members"):
                embed = discord.Embed(title="Error", description="I do not have permission to ban members.", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            if can_moderate(interaction.user, member):
                if duration != None:
                    duration_minutes = await self.parse_temporary_action(member.id, interaction.guild_id, 'ban', duration)
                    await self.save_temporary_action(member.id, interaction.guild_id, 'ban', duration_minutes)
                    expiration = discord.utils.utcnow() + timedelta(minutes=duration_minutes)
                    experation_time = int(expiration.timestamp())
                    expiration_time_str = f"<t:{experation_time}:R>"
                await member.ban(reason=reason)
                if duration != None:
                    await self.send_mod_message(interaction, member, "Ban", reason, expiration_time_str)
                else:
                    await self.send_mod_message(interaction, member, "Ban", reason)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to ban this member.", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to ban this member.", color=discord.Color.red()) 
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.NotFound:
            embed = discord.Embed(title="Error", description="This member was not found.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to ban this member.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="unban", description="Unban a member from the server")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(user_id="The user ID of the member to unban")
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.user.id))
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: Optional[str] = "No reason provided.") -> None:
        guild = interaction.guild
        try:
            await interaction.response.defer()
            if not await bot_has_permission(interaction, "ban_members"):
                embed = discord.Embed(title="Error", description="I do not have permission to unban members.", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            id = int(user_id)
            banned_users = [entry async for entry in interaction.guild.bans()]
            user = discord.Object(id=id)
            ban_entry = next((entry for entry in banned_users if entry.user.id == id), None)
            member = await interaction.client.fetch_user(id)
            if not ban_entry:
                embed = discord.Embed(title="Error", description="This member is not banned.", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            await interaction.guild.unban(user, reason=reason)
            await self.send_mod_message(interaction, member, "Unban", reason)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to unban this member.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.NotFound:
            await interaction.followup.send("User not found in the ban list.", ephemeral=True)
        except discord.HTTPException:
            await interaction.followup.send("Failed to unban the user. Please try again.", ephemeral=True)

    @app_commands.command(name="mute", description="Mute a member in the server")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="The member to mute", reason="The reason for muting the member", duration="The duration of the mute (e.g., 1d, 2h, 30m)")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: Optional[str] = None, reason: str = "No reason provided.") -> None:
        try:
            await interaction.response.defer()
            if not await bot_has_permission(interaction, "manage_roles"):
                embed = discord.Embed(title="Error", description="Missing peemissions: Manage Roles", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            if can_moderate(interaction.user, member):
                if bot_can_moderate(member):
                    mute_role = await get_or_create_mute_role(interaction.guild)
                    if mute_role in member.roles:
                        embed = discord.Embed(title="Error", description=f"{member.mention} is already muted.", color=discord.Color.red())
                        await interaction.followup.send(embed=embed)
                        return
                    if duration != None:
                        duration_minutes = await self.parse_temporary_action(member.id, interaction.guild_id, "mute", duration)
                        await self.save_temporary_action(member.id, interaction.guild_id, "mute", duration_minutes)
                        expiration = discord.utils.utcnow() + timedelta(minutes=duration_minutes)
                        experation_time = int(expiration.timestamp())
                        expiration_time_str = f"<t:{experation_time}:R>"
                    await member.add_roles(mute_role, reason=reason)
                    if duration != None:
                        await self.send_mod_message(interaction, member, "Mute", reason, expiration_time_str)
                    else:
                        await self.send_mod_message(interaction, member, "Mute", reason)
                else:
                    embed = discord.Embed(title="Error", description="I do not have permission to mute this member.", color=discord.Color.red())
                    await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to mute this member.", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to mute this member.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.NotFound:
            embed = discord.Embed(title="Error", description="This member was not found.", color=discord.Color.red())
            await interaction.follow.send(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to mute this member.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="unmute", description="Unmute a member in the server")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="The member to unmute")
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.user.id))
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason provided.") -> None:
        try:
            await interaction.response.defer()
            if not await bot_has_permission(interaction, "manage_roles"):
                discord.Embed(title="Error", description="Missing peemissions: Manage Roles", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            if can_moderate(interaction.user, member):
                if bot_can_moderate(member):
                    mute_role = await get_or_create_mute_role(interaction.guild)
                    if mute_role not in member.roles:
                        embed = discord.Embed(title="Error", description=f"{member.mention} is not muted.", color=discord.Color.red())
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    await member.remove_roles(mute_role, reason="Unmuted by moderator")
                    await self.send_mod_message(interaction, member, "Unmute", reason)
                else:
                    embed = discord.Embed(title="Error", description="I do not have permission to unmute this member.", color=discord.Color.red())
                    await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to unmute this member.", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to unmute this member.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.NotFound:
            embed = discord.Embed(title="Error", description="This member was not found.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to unmute this member.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="The member to warn", reason="The reason for warning the member")
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.user.id))
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided.") -> None:
        try:
            await interaction.response.defer()
            if not await bot_has_permission(interaction, "moderate_members"):
                embed = discord.Embed(title="Error", description="Missing permissions: Moderate Members", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            if can_moderate(interaction.user, member):
                await self.send_mod_message(interaction, member, "Warn", reason)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to warn this member" , color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to warn this member.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="purge", description="Delete a specified number of messages from a channel")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="The number of messages to delete")
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.user.id))
    async def purge(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 50]) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            if not await bot_has_permission(interaction, "manage_messages"):
                embed = discord.Embed(title="Error", description="Missing permissions: Manage Messages", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            deleted = await interaction.channel.purge(limit=amount)
            embed = discord.Embed(title="Purge", description=f"Deleted {len(deleted)} messages.", color=discord.Color.green())
            await interaction.followup.send(embed=embed, ephemeral=True)
            log_embed = discord.Embed(
                title="Bulk Message Deletion",
                description=f"{len(deleted)} messages were purged in {interaction.channel.mention} by {interaction.user.mention}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            log_embed.set_footer(text=f"User ID: {interaction.user.id}", icon_url=interaction.user.avatar.url)
            log_channel_id = self.access_log_channel_id(interaction.guild_id)
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to delete messages.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="lock_channel", description="Lock a channel")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.user.id))
    async def lock_channel(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None) -> None:
        try:
            await interaction.response.defer(thinking=True)
            if channel is None:
                channel = interaction.channel
            required_permissions = ["manage_channels", "send_messages"]
        # Check for missing permissions
            missing_permissions = check_bot_permissions(channel, required_permissions)
            if missing_permissions:
                embed = discord.Embed(
                    title="Error",
                    description=("I do not have the following permissions: " +
                                 ", ".join(missing_permissions)),
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            if interaction.user.guild_permissions.manage_channels:
                await channel.set_permissions(interaction.guild.default_role, send_messages=False)
                embed = discord.Embed(title="Channel Locked", description=f"{channel.mention} has been locked by {interaction.user.mention}.", color=discord.Color.blue())
                await interaction.followup.send(embed=embed)
                if interaction.channel.id != channel.id:
                    await channel.send(embed=embed)
                log_embed = discord.Embed(
                    title="Channel Locked",
                    description=f"{channel.mention} has been locked by {interaction.user.mention}",
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                log_embed.set_footer(text=f"User ID: {interaction.user.id}", icon_url=interaction.user.avatar.url)
                log_channel_id = self.access_log_channel_id(interaction.guild_id)
                if log_channel_id:
                    log_channel = self.bot.get_channel(log_channel_id)
                    if log_channel:
                        await log_channel.send(embed=log_embed)
            if not interaction.user.guild_permissions.manage_channels:
                embed = discord.Embed(title="Error", description="You do not have permission to lock channels.", color=discord.Color.red())
                await interaction.followup.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to lock channels.", color=discord.Color.red())
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}", color=discord.Color.red())
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="unlock_channel", description="Unlock a channel")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.user.id))
    async def unlock_channel(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None) -> None:
        try:
            await interaction.response.defer(thinking=True)
            if channel is None:
                channel = interaction.channel
            required_permissions = ["manage_channels", "send_messages"]
        # Check for missing permissions
            missing_permissions = check_bot_permissions(channel, required_permissions)
            if missing_permissions:
                embed = discord.Embed(
                    title="Error",
                    description=("I do not have the following permissions: " +
                                 ", ".join(missing_permissions)),
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            if interaction.user.guild_permissions.manage_channels:
                await channel.set_permissions(interaction.guild.default_role, send_messages=True)
                embed = discord.Embed(title="Channel Unlocked", description=f"{channel.mention} has been unlocked by {interaction.user.mention}.", color=discord.Color.blue())
                await interaction.followup.send(embed=embed)
                if interaction.channel.id != channel.id:
                    await channel.send(embed=embed)
                log_embed = discord.Embed(
                    title="Channel Unlocked",
                    description=f"{channel.mention} has been unlocked by {interaction.user.mention}",
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                log_embed.set_footer(text=f"User ID: {interaction.user.id}", icon_url=interaction.user.avatar.url)
                log_channel_id = self.access_log_channel_id(interaction.guild_id)
                if log_channel_id:
                    log_channel = self.bot.get_channel(log_channel_id)
                    if log_channel:
                        await log_channel.send(embed=log_embed)
            if not interaction.user.guild_permissions.manage_channels:
                embed = discord.Embed(title="Error", description="You do not have permission to unlock channels.", color=discord.Color.red())
                await interaction.followup.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to unlock channels.", color=discord.Color.red())
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}", color=discord.Color.red())
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="addrole", description="Add a role to a member")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(member="The member to add the role to", role="The role to add")
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.user.id))
    async def addrole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role) -> None:
        try:
            await interaction.response.defer(thinking=True)
            if can_moderate_roles(interaction.user, role):
                if bot_can_moderate_roles(role):
                    await member.add_roles(role, reason=f"Added by {interaction.user}")
                    await self.send_mod_message(interaction, member, "Add Role", f"Added the role {role.mention} to {member.mention}")
                else:
                    embed = discord.Embed(title="Error", description="I do not have permission to add this role.", color=discord.Color.red())
                    await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to add this role.", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to add this role.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to add this role.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    @app_commands.command(name="removerole", description="Remove a role from a member")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(member="The member to remove the role from", role="The role to remove")
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.user.id))
    async def removerole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role) -> None:
        try:
            await interaction.response.defer(thinking=True)
            if can_moderate_roles(interaction.user, role):
                if bot_can_moderate_roles(role):
                    if can_moderate(interaction.user, member):
                        await member.remove_roles(role, reason=f"Removed by {interaction.user}")
                        await self.send_mod_message(interaction, member, "Remove Role", f"Removed the role {role.mention} from {member.mention}")
                    else:
                        embed = discord.Embed(title="Error", description="You do not have permission to remove roles from this member.", color=discord.Color.red())
                        await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(title="Error", description="I do not have permission to remove this eole.", color=discord.Color.red())
                    await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to remove this role.", color=discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to remove this role.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to remove this role.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="lockdown_server", description="Lockdown or unlock the server channels")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.user.id))
    async def lockdown_server(self, interaction: discord.Interaction, action: Literal["lock", "unlock"]):
        try:
            await interaction.response.defer(thinking=True)  
            if not interaction.user.guild_permissions.manage_channels:
                embed = discord.Embed(
                    title="Error",
                    description="You do not have permission to manage channels.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            guild = interaction.guild
            action_description = "locked" if action == "lock" else "unlocked"
            send_messages_permission = False if action == "lock" else True
            channels = []
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    required_permissions = ["manage_channels", "send_messages"]
                    missing_permissions = check_bot_permissions(channel, required_permissions)

                    if missing_permissions:
                        channels.append(channel)
                    else:
                        await channel.set_permissions(guild.default_role, send_messages=send_messages_permission)
                    await asyncio.sleep(1)

            embed = discord.Embed(
                title=f"Server {action_description.capitalize()}",
                description=f"All text channels have been {action_description}.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            if channels:
                embed.add_field(name="I could not lock the following channels:", value="\n".join(f"#{channel.mention}" for channel in channels), inline=False)
            embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
            embed.set_thumbnail(url=guild.icon.url)
            await interaction.followup.send(embed=embed)
            log_channnel_id = self.access_log_channel_id(interaction.guild_id)
            if log_channnel_id:
                log_channel = self.bot.get_channel(log_channnel_id)
                if log_channel:
                    await log_channel.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
        )
            await interaction.followup.send(embed=embed, ephemeral=True)
        

    @app_commands.command(name="history", description="View moderation action history")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="The member to view history for", action="The action to view history for", moderator="The moderator to view history for", user_id="The user ID to view history for")
    async def history(self, interaction: discord.Interaction, member: Optional[discord.Member] = None, action: Optional[str] = None, moderator: Optional[discord.Member] = None, user_id: Optional[int] = None) -> None:
        try:
            await interaction.response.defer(thinking=True)
            if not interaction.user.guild_permissions.moderate_members:
                embed = discord.Embed(
                    title="Error",
                    description="You do not have permission to view moderation action history.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            if member or action or moderator or user_id is not None:
                if member or action or moderator is not None:
                    log = await moderation_log_fetch(interaction.guild, member.id, action, moderator)
                if user_id is not None:
                    user = self.bot.get_user(user_id)
                    log = await moderation_log_fetch(interaction, user, action, moderator)
            else:
                log = await moderation_log_fetch(interaction.guild)
            if log:
                pages: List[discord.Embed] = []
                for embed in log:
                    pages.append(embed)
                paginator = ButtonPaginator(pages=pages, author_id=interaction.user.id)
                message = await interaction.followup.send(embed=pages[0], view=paginator)
                paginator.message = message
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))