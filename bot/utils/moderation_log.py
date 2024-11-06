import discord
from discord.ext import commands
from typing import Optional, List
from datetime import datetime
import aiosqlite

moderation_logs = 'data/moderation_log.db'

async def moderation_log(guild, user: discord.Member, action, reason, moderator, duration = None) -> None:
    async with aiosqlite.connect(moderation_logs) as db:
        await db.execute('CREATE TABLE IF NOT EXISTS moderation_log (guild_id INTEGER, user_id INTEGER, action TEXT, reason TEXT, moderator_id INTEGER, timestamp TEXT, duration TEXT)')
        await db.execute('INSERT INTO moderation_log (guild_id, user_id, action, reason, moderator_id, timestamp, duration) VALUES (?, ?, ?, ?, ?, ?, ?)', (guild.id, user.id, action, reason, moderator.id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), duration))
        await db.commit()

async def moderation_log_fetch(guild, user: Optional[discord.Member] = None, action: Optional[str] = None, moderator: Optional[discord.Member] = None) -> List[discord.Embed]:
    if user and action or moderator and action or user and moderator is not None:
        return [discord.Embed(title='ERROR', description='You can only search for one of the following: member, action, moderator, user_id', color=discord.Color.red())]
    if user or moderator or action is not None:
        async with aiosqlite.connect(moderation_logs) as db:
            if action is not None:
                async with db.execute('SELECT * FROM moderation_log WHERE guild_id = ? AND action = ?', (guild.id, action)) as cursor:
                    log = await cursor.fetchall()
            if moderator is not None:
                async with db.execute('SELECT * FROM moderation_log WHERE guild_id = ? AND moderator_id = ?', (guild.id, moderator.id)) as cursor:
                    log = await cursor.fetchall()
            if user is not None:
                async with db.execute('SELECT * FROM moderation_log WHERE guild_id = ? AND user_id = ?', (guild.id, user)) as cursor:
                    log = await cursor.fetchall()
    else:
        async with aiosqlite.connect(moderation_logs) as db:
            async with db.execute('SELECT * FROM moderation_log WHERE guild_id = ? ORDER BY timestamp DESC', (guild.id,)) as cursor:
                log = await cursor.fetchall()
    if not log:
        return [discord.Embed(title='ERROR', description='No moderation logs found for this search parameter.', color=discord.Color.red())]
    if log:
        embeds = []
        for i in range(0, len(log), 10):
            embed = discord.Embed(title='Moderation Log', color=discord.Color.blue())
            for j in range(i, min(i + 10, len(log))):
                embed.add_field(name=f'Case #{j + 1}', value=f'**User:** <@{log[j][1]}> ({log[j][1]})\n**Action:** {log[j][2]}\n**Reason:** {log[j][3]}\n**Moderator:** <@{log[j][4]}> ({log[j][4]})\n**Timestamp:** {log[j][5]}\n**Duration:** {log[j][6]}')
            embeds.append(embed)
        return embeds