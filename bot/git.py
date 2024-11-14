from discord.ext import commands
import discord
from flask import Flask, request, jsonify
import threading
import json

app = Flask(__name__)

class GitHubUpdateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_channel_id = None  # This will hold the channel ID for updates

    @commands.command(name='setupdatechannel', help='Set the channel for GitHub updates')
    @commands.has_permissions(administrator=True)
    async def set_update_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel where updates will be posted"""
        self.update_channel_id = channel.id
        await ctx.send(f'Update channel set to {channel.mention}')

    async def post_update(self, commit_data):
        if self.update_channel_id:
            channel = self.bot.get_channel(self.update_channel_id)
            if channel:
                embed = discord.Embed(
                    title="New GitHub Commit",
                    description=commit_data['head_commit']['message'],
                    url=commit_data['head_commit']['url'],
                    color=discord.Color.green()
                )
                embed.add_field(name="Author", value=commit_data['head_commit']['author']['name'])
                await channel.send(embed=embed)

    def run_flask(self):
        @app.route('/github', methods=['POST'])
        def github_webhook():
            data = request.json
            if 'head_commit' in data:
                self.bot.loop.create_task(self.post_update(data))
            return jsonify({'status': 'received'})

        app.run(port=9329)

    def start_flask_thread(self):
        threading.Thread(target=self.run_flask).start()

async def setup(bot):
    cog = GitHubUpdateCog(bot)
    await bot.add_cog(cog)
    cog.start_flask_thread()