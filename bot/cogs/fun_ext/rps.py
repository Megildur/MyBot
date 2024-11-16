import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import aiosqlite
import random

wins = {}
loss = {}
ties = {}
user_choice = {}

class RockPaperScissors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("RPS loaded")

    async def cog_load(self):
        async with aiosqlite.connect("data/rps.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute("CREATE TABLE IF NOT EXISTS rps (user_id INTEGER PRIMARY KEY, wins INTEGER, loss INTEGER, ties INTEGER)")
                await db.commit()

    async def rpss(self, interaction: discord.Interaction):
        if interaction.user.id not in wins:
            await self.setup_rps(interaction.user.id)
        embed = discord.Embed(title="Rock-Paper-Scissors", description="Choose your move:", color=0x00ff00)
        if interaction.user.id in wins and interaction.user.id in loss and interaction.user.id in ties:
            embed.add_field(name=f"{interaction.user.display_name}'s Stats:", value='\u200b', inline=False)
            embed.add_field(name="Wins:", value=f"{wins[interaction.user.id]}", inline=True)
            embed.add_field(name="Losses:", value=f"{loss[interaction.user.id]}", inline=True)
            embed.add_field(name="Ties:", value=f"{ties[interaction.user.id]}", inline=True)
        view = RockPaperScissorsView(user_id=interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)
        
    async def setup_rps(self, user_id):
        async with aiosqlite.connect("data/rps.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute("SELECT * FROM rps WHERE user_id=?", (user_id,))
                result = await cursor.fetchone()
                if result is None:
                    await cursor.execute("INSERT INTO rps (user_id, wins, loss, ties) VALUES (?, ?, ?, ?)", (user_id, 0, 0, 0))
                    await db.commit()
                else:
                    wins[user_id] = result[1]
                    loss[user_id] = result[2]
                    ties[user_id] = result[3]
    
class RockPaperScissorsView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        
        self.value = None
        self.user_id = user_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot press these buttons while someone else is playing!", ephemeral=True)
            return False
        return True

    @discord.ui.button(
        label="Rock",
        emoji="🪨",
        custom_id="rockself",
        style=discord.ButtonStyle.primary
    )
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "rock"
        await self.process_choice(interaction)

    @discord.ui.button(
        label="Paper", 
        emoji="📄",
        custom_id="paperself",
        style=discord.ButtonStyle.primary
    )
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "paper"
        await self.process_choice(interaction)

    @discord.ui.button(
        label="Scissors", 
        emoji="✂️",
        custom_id="scissorsself",
        style=discord.ButtonStyle.primary
    )
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "scissors"
        await self.process_choice(interaction)

    async def process_choice(self, interaction: discord.Interaction):
        if interaction.user.id not in wins:
            await self.setup_rps(interaction.user.id)
        choices = ["rock", "paper", "scissors"]
        bot_choice = random.choice(choices)
        tie = "It's a tie!"
        win = f"{interaction.user.display_name} wins!"
        lose = f"{interaction.user.display_name} loses!"

        if self.value == bot_choice:
            result = tie
        elif (self.value == "rock" and bot_choice == "scissors") or \
             (self.value == "paper" and bot_choice == "rock") or \
             (self.value == "scissors" and bot_choice == "paper"):
            result = win
        else:
            result = lose

        if result == win:
            wins[interaction.user.id] += 1
        elif result == lose:
            loss[interaction.user.id] += 1
        else:
            ties[interaction.user.id] += 1
        await self.update_stats(interaction.user.id, wins[interaction.user.id], loss[interaction.user.id], ties[interaction.user.id])
        
        embed = discord.Embed(
            title="Rock-Paper-Scissors", 
            description=f"{interaction.user.display_name} chose {self.value}, Botzilla chose {bot_choice}. {result}",
            color=0x00ff00
        )
        embed.add_field(name=f"{interaction.user.display_name}'s Stats:", value='\u200b', inline=False)
        embed.add_field(name="Wins:", value=f"{wins[interaction.user.id]}", inline=True)
        embed.add_field(name="Losses:", value=f"{loss[interaction.user.id]}", inline=True)
        embed.add_field(name="Ties:", value=f"{ties[interaction.user.id]}", inline=True)
        view=RockPaperScissorsPlayAgainView(user_id=interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)

    async def setup_rps(self, user_id):
        async with aiosqlite.connect("data/rps.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute("SELECT * FROM rps WHERE user_id=?", (user_id,))
                result = await cursor.fetchone()
                if result is None:
                    await cursor.execute("INSERT INTO rps (user_id, wins, loss, ties) VALUES (?, ?, ?, ?)", (user_id, 0, 0, 0))
                    await db.commit()
                    wins.setdefault(user_id, 0)
                    loss.setdefault(user_id, 0)
                    ties.setdefault(user_id, 0)
                else:
                    wins[user_id] = result[1]
                    loss[user_id] = result[2]
                    ties[user_id] = result[3]

    async def update_stats(self, user_id, win, lose, tie):
        async with aiosqlite.connect("data/rps.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute("UPDATE rps SET wins=?, loss=?, ties=? WHERE user_id=?", (win, lose, tie, user_id))
                    
                await db.commit()

class ButtonOnCooldown(commands.CommandError):
    def __init__(self, retry_after: float) -> None:
        self.retry_after = retry_after

def key(interaction: discord.Interaction) -> int:
    return interaction.user.id

global_cooldown_f = commands.CooldownMapping.from_cooldown(1, 5, key)

async def error_handler(interaction: discord.Interaction, error: commands.CommandError) -> None:
    retry_after_hours = round(error.retry_after / 3600)
    retry_after_minutes = round(error.retry_after / 60)
    if error.retry_after >= 3600:  # More than an hour
        message = f"You're on cooldown. Try again in {retry_after_hours} hour{'s' if retry_after_hours > 1 else ''}."
    elif error.retry_after >= 60:  # More than a minute
        message = f"You're on cooldown. Try again in {retry_after_minutes} minute{'s' if retry_after_minutes > 1 else ''}."
    else:  # Seconds
        message = f"You're on cooldown. Try again in {round(error.retry_after):.2f} second{'s' if error.retry_after > 1 else ''}."
    embed = discord.Embed(title="Error", description=message, color=0xff0000)
    await interaction.response.send_message(embed=embed, ephemeral=True)     

class RockPaperScissorsPlayAgainView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.value = None
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        retry_after = global_cooldown_f.update_rate_limit(interaction)
        if retry_after:
            raise ButtonOnCooldown(retry_after)
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        if isinstance(error, ButtonOnCooldown):
            await error_handler(interaction, error)
        else:
            await super().on_error(interaction, error, item)

    @discord.ui.button(
        label="Play Again", 
        emoji="🔄",
        custom_id="play_again_rps_self",
        style=discord.ButtonStyle.primary
    )
    async def play_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        if interaction.user.id not in wins:
            await self.setup_rps(interaction.user.id)
        await self.rock_paper_scissors(interaction)

    async def rock_paper_scissors(self, interaction: discord.Interaction):      
        embed = discord.Embed(title="Rock-Paper-Scissors", description="Choose your move:", color=0x00ff00)
        if interaction.user.id in wins:
            embed.add_field(name=f"{interaction.user.display_name}\'s Stats:", value='\u200b', inline=False)
            embed.add_field(name="Wins:", value=f"{wins[interaction.user.id]}", inline=True)
            embed.add_field(name="Losses:", value=f"{loss[interaction.user.id]}", inline=True)
            embed.add_field(name="Ties:", value=f"{ties[interaction.user.id]}", inline=True)
        view = RockPaperScissorsView(user_id=interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)

    async def setup_rps(self, user_id):
        async with aiosqlite.connect("data/rps.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute("SELECT * FROM rps WHERE user_id=?", (user_id,))
                result = await cursor.fetchone()
                if result is None:
                    await cursor.execute("INSERT INTO rps (user_id, wins, loss, ties) VALUES (?, ?, ?, ?)", (user_id, 0, 0, 0))
                    await db.commit()
                else:
                    wins[user_id] = result[1]
                    loss[user_id] = result[2]
                    ties[user_id] = result[3]
            
async def setup(bot):
    await bot.add_cog(RockPaperScissors(bot))
    bot.add_view(RockPaperScissorsView(user_id=None))
    bot.add_view(RockPaperScissorsPlayAgainView(user_id=None))