import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
from typing import Optional, Literal
from bot.utils.mod_helpers import mod_build_embed, can_moderate, get_or_create_mute_role, bot_can_moderate, can_moderate_roles, bot_can_moderate_roles, parse_duration
from datetime import datetime, timedelta
import asyncio

persistent_data = "data/persistent_data.db"

class Moderation(commands.GroupCog, group_name="mod"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_expired_actions.start()

    async def cog_load(self) -> None:
        await self.initialize_database()

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
    async def check_expired_actions(self):
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
                            elif action_type == 'ban':
                                user = discord.Object(user_id)
                                await guild.unban(user)
                                log_channel_id = self.access_log_channel_id(guild_id)
                                if log_channel_id:
                                    log_channel = guild.get_channel(log_channel_id)
                                    if log_channel:
                                        embed = await mod_build_embed("Unban", member, self.bot.user, f"Ban duration expired for user")
                                        await log_channel.send(embed=embed)
                        await db.execute(
                            "DELETE FROM temporary_actions WHERE user_id = ? AND guild_id = ? AND action_type = ?",
                            (user_id, guild_id, action_type)
                        )
                        await db.commit()
            await asyncio.sleep(60)

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

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(member="The member to kick", reason="The reason for kicking the member")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided.") -> None:
        try:
            if can_moderate(interaction.user, member):
                await member.kick(reason=reason)
                embed = await mod_build_embed("kick", member, interaction.user, reason)
                await interaction.response.send_message(embed=embed)
                log_channel_id = self.access_log_channel_id(interaction.guild_id)
                if log_channel_id:
                    log_channel = self.bot.get_channel(log_channel_id)
                    if log_channel:
                        await log_channel.send(embed=embed)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to kick this member.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to kick this member.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.NotFound:
            embed = discord.Embed(title="Error", description="This member was not found.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to kick this member.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(member="The member to ban", reason="The reason for banning the member", duration="The duration of the ban (e.g., 1d, 2h, 30m)")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, duration: Optional[str] = None, reason: str = "No reason provided.") -> None:
        try:
            if can_moderate(interaction.user, member):
                if duration != None:
                    duration_minutes = await self.parse_temporary_action(member.id, interaction.guild_id, 'ban', duration)
                    await self.save_temporary_action(member.id, interaction.guild_id, 'ban', duration_minutes)
                    expiration = discord.utils.utcnow() + timedelta(minutes=duration_minutes)
                    experation_time = int(expiration.timestamp())
                    expiration_time_str = f"<t:{experation_time}:R>"
                    embed = await mod_build_embed("Ban", member, interaction.user, reason, expiration_time_str)
                else:
                    embed = await mod_build_embed("Ban", member, interaction.user, reason, duration)
                await member.ban(reason=reason)
                await interaction.response.send_message(embed=embed)
                log_channel_id = self.access_log_channel_id(interaction.guild_id)
                if log_channel_id:
                    log_channel = self.bot.get_channel(log_channel_id)
                    if log_channel:
                        await log_channel.send(embed=embed)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to ban this member.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to ban this member.", color=discord.Color.red()) 
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.NotFound:
            embed = discord.Embed(title="Error", description="This member was not found.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to ban this member.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unban", description="Unban a member from the server")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(user_id="The user ID of the member to unban")
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: Optional[str] = "No reason provided.") -> None:
        guild = interaction.guild
        try:
            id = int(user_id)
            banned_users = [entry async for entry in interaction.guild.bans()]
            user = discord.Object(id=id)
            ban_entry = next((entry for entry in banned_users if entry.user.id == id), None)
            member = self.bot.get_user(id)

            if not ban_entry:
                embed = discord.Embed(title="Error", description="This member is not banned.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            await interaction.guild.unban(user, reason=reason)
            embed = await mod_build_embed("unban", member, interaction.user, reason)
            await interaction.response.send_message(embed=embed)
            log_channel_id = self.access_log_channel_id(interaction.guild_id)
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    await log_channel.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to unban this member.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("User not found in the ban list.", ephemeral=True)
        except discord.HTTPException:
            await interaction.response.send_message("Failed to unban the user. Please try again.", ephemeral=True)

    @app_commands.command(name="mute", description="Mute a member in the server")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="The member to mute", reason="The reason for muting the member", duration="The duration of the mute (e.g., 1d, 2h, 30m)")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: Optional[str] = None, reason: str = "No reason provided.") -> None:
        try:
            await interaction.response.defer()
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
                        embed = await mod_build_embed("mute", member, interaction.user, reason, expiration_time_str)
                    else:
                        embed = await mod_build_embed("mute", member, interaction.user, reason)
                    await member.add_roles(mute_role, reason=reason)
                    await interaction.followup.send(embed=embed)
                    log_channel_id = self.access_log_channel_id(interaction.guild_id)
                    if log_channel_id:
                        log_channel = self.bot.get_channel(log_channel_id)
                        if log_channel:
                            await log_channel.send(embed=embed)
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
    async def unmute(self, interaction: discord.Interaction, member: discord.Member) -> None:
        try:
            await interaction.response.defer()
            if can_moderate(interaction.user, member):
                if bot_can_moderate(member):
                    mute_role = await get_or_create_mute_role(interaction.guild)
                    if mute_role not in member.roles:
                        embed = discord.Embed(title="Error", description=f"{member.mention} is not muted.", color=discord.Color.red())
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    await member.remove_roles(mute_role, reason="Unmuted by moderator")
                    embed = await mod_build_embed("unmute", member, interaction.user, "Moderator unmuted")
                    await interaction.followup.send(embed=embed)
                    log_channel_id = self.access_log_channel_id(interaction.guild_id)
                    if log_channel_id:
                        log_channel = self.bot.get_channel(log_channel_id)
                        if log_channel:
                            await log_channel.send(embed=embed)
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
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided.") -> None:
        try:
            if can_moderate(interaction.user, member):
                embed = await mod_build_embed("Warn", member, interaction.user, reason)
                await interaction.response.send_message(embed=embed)
                log_channel_id = self.access_log_channel_id(interaction.guild_id)
                if log_channel_id:
                    log_channel = self.bot.get_channel(log_channel_id)
                    if log_channel:
                        await log_channel.send(embed=embed)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to warn this member" , color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to warn this member.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="purge", description="Delete a specified number of messages from a channel")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="The number of messages to delete")
    async def purge(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 1000]) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=amount)
            embed = discord.Embed(
                title="Messages Purged",
                description=f"Successfully deleted {len(deleted)} messages.",
                color=discord.Color.blue()
            )
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
    async def lock_channel(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None) -> None:
        pass

    @app_commands.command(name="unlock_channel", description="Unlock a channel")
    @app_commands.default_permissions(manage_channels=True)
    async def unlock_channel(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None) -> None:
        pass

    @app_commands.command(name="addrole", description="Add a role to a member")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(member="The member to add the role to", role="The role to add")
    async def addrole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role) -> None:
        try:
            if can_moderate_roles(interaction.user, role):
                if bot_can_moderate_roles(role):
                    pass
                else:
                    embed = discord.Embed(title="Error", description="I do not have permission to add this role.", color=discord.Color.red())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to add this role.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to add this role.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to add this role.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
    @app_commands.command(name="removerole", description="Remove a role from a member")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(member="The member to remove the role from", role="The role to remove")
    async def removerole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role) -> None:
        try:
            if can_moderate_roles(interaction.user, role):
                if bot_can_moderate_roles(role):
                    if can_moderate(interaction.user, member):
                        pass
                    else:
                        embed = discord.Embed(title="Error", description="You do not have permission to remove roles from this member.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(title="Error", description="I do not have permission to remove this eole.", color=discord.Color.red())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="Error", description="You do not have permission to remove this role.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I do not have permission to remove this role.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(title="Error", description="An error occurred while trying to remove this role.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="lockdown_server", description="Lockdown the server")
    @app_commands.default_permissions(manage_channels=True)
    async def lockdown_server(self, interaction: discord.Interaction, action: Literal["lock", "unlock"]):
        pass

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))