import discord
from typing import Optional
import re

async def mod_build_embed(action: str, member: discord.Member, moderator: discord.Member, reason: str = None, duration: Optional[str] = None) -> discord.Embed:
    embed = discord.Embed(title=f"Moderator Action: {action}", color=discord.Color.red(), timestamp=discord.utils.utcnow())
    embed.add_field(name="Target", value=f"{member.mention} ({member.id})", inline=False)
    embed.add_field(name="Moderator", value=f"{moderator.mention} ({moderator.id})", inline=False)
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)
    if duration:
        embed.add_field(name="Duration", value=duration, inline=False)
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"User ID: {member.id} | Action time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", icon_url=moderator.avatar.url)
    return embed

def parse_duration(duration_str: str) -> Optional[int]:
    if not duration_str:
        return None
    if isinstance(duration_str, int):
        return duration_str
    duration_regex = r'(?:(\d+)w)?(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?$'
    match = re.match(duration_regex, duration_str.lower().strip())
    if not match:
        return None
    weeks, days, hours, minutes = map(lambda x: int(x) if x else 0, match.groups())
    total_minutes = (weeks * 7 * 24 * 60) + (days * 24 * 60) + (hours * 60) + minutes
    return total_minutes if total_minutes > 0 else None

def can_moderate(moderator: discord.Member, member: discord.Member) -> bool:
    return (moderator.top_role.position > member.top_role.position and member != moderator and member != moderator.guild.owner and member != moderator.guild.me)

def bot_can_moderate(member: discord.Member) -> bool:
    return (member.guild.me.top_role.position > member.top_role.position)

def can_moderate_roles(moderator: discord.Member, role: discord.Role) -> bool:
    return (moderator.top_role.position > role.position and role != moderator.guild.default_role and role != moderator.guild.me.top_role)

def bot_can_moderate_roles(role: discord.Role) -> bool:
    return (role.guild.me.top_role.position > role.position)

async def get_or_create_mute_role(guild: discord.Guild) -> discord.Role:
    mute_role = discord.utils.get(guild.roles, name="Muted")
    if not mute_role:
        permissions = discord.Permissions(send_messages=False, speak=False)
        mute_role = await guild.create_role(name="Muted", reason="Mute role for muting members", permissions=permissions)
        for channel in guild.channels:
            await channel.set_permissions(mute_role, send_messages=False, speak=False)
    return mute_role