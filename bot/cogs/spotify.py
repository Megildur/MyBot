import discord
from discord.ext import commands
from discord import app_commands
from discord import Spotify, Activity, ActivityType
from typing import Optional

class SpotifyCog(commands.GroupCog, name="spotify"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="now_playing", description="Shows the currently playing song for a user. Defaults to user using command. (Spotify only)")
    async def now_playing(self, interaction: discord.Interaction, add_a_message: Optional[str] = None, user: discord.Member = None):
        guild = interaction.guild
        if user is None:
            user = guild.get_member(interaction.user.id)
        else:
            user = guild.get_member(user.id)
        spotify_result = next((activity for activity in user.activities if isinstance(activity, Spotify)), None)
        if spotify_result is None:
            await interaction.response.send_message(f"{user.mention} is not listening to Spotify.", ephemeral=True)
            return
        duration = spotify_result.duration
        time = str(duration)
        embed = discord.Embed(title="Now Playing", description=f"{user.mention} is listening to:", color=0x1db954)
        song_url = f"https://open.spotify.com/track/{spotify_result.track_id}"
        embed.add_field(name=f"{spotify_result.title} by {spotify_result.artist} from the album {spotify_result.album} - {time[:-7]}", value=f"Listen on Spotify: [Click here]({song_url})", inline=False)
        embed.set_thumbnail(url=spotify_result.album_cover_url)
        if add_a_message is not None:
            message = add_a_message
            await interaction.response.send_message(f'{message}', embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SpotifyCog(bot))

   