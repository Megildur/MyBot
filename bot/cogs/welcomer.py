import discord
from discord.ext import commands
import os
import easy_pil
import random
import aiosqlite

welcomer = "data/welcomer.db"

class Welcomer(commands.GroupCog, name="welcomer")
    def __init__(self, bot):
        self.bot = bot
        self.enable = {}
        self.channel = {}
        self.message = {}
        self.image = {}
        self.auto_role = {}

    async def cog_load(self):
        async with aiosqlite.connect(welcomer) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS wlcmer (guild_id INTEGER, enable INTEGER, channel_id INTEGER, message TEXT, image TEXT, role_id INTEGER, PRIMARY KEY (guild_id, enable))"
            )
            await db.commit()
            await db.close()

    async def load_vars(self, guild_id):
        async with aiosqlite.connect(welcomer) as db:
            cursor = await db.execute("SELECT * FROM wlcmer WHERE guild_id = ?", (guild_id,))
            data = await cursor.fetchone()
            await db.close()
            if data:
                self.enable[guild_id] = data[1]
                self.channel[guild_id] = data[2]
                self.message[guild_id] = data[3]
                self.image[guild_id] = data[4]
                self.auto_role[guild_id] = data[5]
            else:
                self.enable[guild_id] = 0
                self.auto_role[guild_id] = 0
            
    @commands.Cog.listener()
    async def on_gulid_join(self, guild):
        async with aiosqlite.connect(welcomer) as db:
            await db.execute(
                "INSERT INTO wlcmer (guild_id, enable, channel_id, message, image, role_id) VALUES (?, ?, ?, ?, ?, ?)",
                (guild.id, 0, 0, 0, 0, 0),
            )
            await db.commit()
            await db.close()
            await self.load_vars(guild.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id not in self.enable:
            await self.load_vars(member.guild.id)
        if self.auto_role[member.guild.id] != 0:
            role = member.guild.get_role(self.auto_role[member.guild.id])
            await member.add_roles(role)
        if self.enable[member.guild.id] == 0:
            return
        welcome_channel = self.channel[member.guild.id]
        if welcome_channel == 0:
            return
        if self.image[member.guild.id] == 0:
            images = [image for image in os.listdir("./data/images/default")]
        else:
            images = [image for image in os.listdir(f"./data/images/{member.guild.id}")]
        random_image = random.choice(images)
        if self.image[member.guild.id] == 0:
            bg = easy_pil.Editor(f'./data/images/default/{random_image}').resize((1920, 1080))
        else:
            bg = easy_pil.Editor(f'./data/images/{member.guild.id}/{random_image}').resize((1920, 1080))
        avatar_image = await easy_pil.load_image_async(str(member.avatar.url))
        avatar = easy_pil.Editor(avatar_image).resize((200, 200)).circle_image()

        big_font = easy_pil.Font.poppins(size=90, variant="bold")
        small_font = easy_pil.Font.poppins(size=60, variant="regular")

        bg.paste(avatar, (835, 340))
        bg.ellipse((835, 340), 250, 250, outline="white", stroke_width=5)
        bg.text((960, 620), f"Welcome to {member.guild.name}", font=big_font, color="white", align="center")
        bg.text((960, 740), f"{member.name} is member #{member.guild.member_count}!", font=small_font, color="white", align="center")
        img_file = discord.File(fp=bg.image_bytes, filename=random_image)
        if self.message[member.guild.id] == 0:
            await welcome_channel.send(f"Welcome {member.mention}! Please make sure to read the rules! Thankyou for joining our server!", file=img_file)
        else:
            await welcome_channel.send(self.message[member.guild.id].format(_mention=member.mention, _name=member.name), file=img_file)

async def setup(bot):
    await bot.add_cog(Welcomer(bot))