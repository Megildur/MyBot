import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncpraw as praw
import os
import dotenv
from dotenv import load_dotenv

load_dotenv()

SECRET = str(os.getenv('SECRET'))
SCRIPT = str(os.getenv('SCRIPT'))

class Reddit(commands.GroupCog, group_name="reddit"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.reddit = praw.Reddit(client_id=SCRIPT, client_secret=SECRET, user_agent="script:Botzilla:v1.0 (by u/Same_Doubt_6585)")

    @app_commands.command(name="meme", description="Get a random meme from Reddit")
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def meme(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        subreddit = await self.reddit.subreddit("memes")
        post_list = []
        async for post in subreddit.hot(limit=25):
            if not post.over_18 and post.author is not None and any(post.url.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif")):
                author_name = post.author.name
                title = post.title
                post_list.append((post.url, author_name, title))
            if post.author is None:
                author_name = "Unknown"
                title = post.title
                post_list.append((post.url, author_name, title))
        if post_list:
            meme = random.choice(post_list)
            embed = discord.Embed(title=meme[2], description=meme[1], color=discord.Color.blue())
            embed.set_author(name=f"Meme requested by {interaction.user.name}", icon_url=self.bot.user.avatar.url)
            embed.set_image(url=meme[0])
            embed.set_footer(text=f"Post created by {meme[1]}.", icon_url=None)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("No memes found in the subreddit.")

    def cog_unload(self) -> None:
        self.bot.loop.create_task(self.reddit.close())

async def setup(bot) -> None:
    await bot.add_cog(Reddit(bot))