import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import random
from typing import Optional, Literal

economy = 'data/economy.db'

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class Economy(commands.GroupCog, group_name="economy"):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        async with aiosqlite.connect(economy) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS economy (user_id INTEGER PRIMARY KEY, balance INTEGER, bank INTEGER)")
            await db.commit()

    async def prime_db(self, user_id: int) -> None:
        async with aiosqlite.connect(economy) as db:
            await db.execute("INSERT OR IGNORE INTO economy (user_id, balance, bank) VALUES (?, ?, ?)", (user_id, 0, 0))
            await db.commit()

    balance = app_commands.Group(name="balance", description="Wallet commands")
    
    @balance.command(name="wallet", description="Check your wallet balance")
    async def wallet(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(economy) as db:
            cursor = await db.execute("SELECT balance FROM economy WHERE user_id = ?", (interaction.user.id,))
            balance = await cursor.fetchone()
            if balance is None:
                await self.prime_db(interaction.user.id)
            embed = discord.Embed(title="Wallet Balance:", description=f"Your wallet balance is {balance[0]} coins 🪙", color=discord.Color.green())
            embed.set_thumbnail(url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily reward")
    @app_commands.checks.cooldown(1, 86400, key=lambda i: (i.user.id))
    async def daily(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(economy) as db:
            cursor = await db.execute("SELECT balance FROM economy WHERE user_id = ?", (interaction.user.id,))
            balance = await cursor.fetchone()
            if balance is None:
                await self.prime_db(interaction.user.id)
                balance = (0,)
            reward = random.randint(100, 500)
            await db.execute("UPDATE economy SET balance = balance + ? WHERE user_id = ?", (reward, interaction.user.id))
            await db.commit()
            embed = discord.Embed(title="Daily Reward🤑", description=f"You claimed your daily reward of {reward} coins 🪙!", color=discord.Color.green())
            embed.add_field(name="New Wallet Balance:", value=f"{balance[0] + reward} coins 🪙")
            embed.set_thumbnail(url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="deposit", description="Deposit coins into your bank")
    async def deposit(self, interaction: discord.Interaction, amount: int) -> None:
        async with aiosqlite.connect(economy) as db:
            cursor = await db.execute("SELECT balance FROM economy WHERE user_id = ?", (interaction.user.id,))
            balance = await cursor.fetchone()
            if balance is None:
                await self.prime_db(interaction.user.id)
                balance = (0,)
            if amount > balance[0]:
                embed = discord.Embed(title="Deposit", description="You don't have enough coins to deposit that much.", color=discord.Color.red())
                embed.set_thumbnail(url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed)
                return
            await db.execute("UPDATE economy SET balance = balance - ?, bank = bank + ? WHERE user_id = ?", (amount, amount, interaction.user.id))
            await db.commit()
            embed = discord.Embed(title="Deposit 🏧", description=f"You deposited {amount} coins into your bank 🏦.", color=discord.Color.green())
            embed.add_field(name="New Wallet Balance:", value=f"{balance[0] - amount} coins 🪙")
            embed.add_field(name="New Bank Balance:", value=f"{balance[0] + amount} coins 💳")
            embed.set_thumbnail(url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="withdraw", description="Withdraw coins from your bank")
    async def withdraw(self, interaction: discord.Interaction, amount: int) -> None:
        async with aiosqlite.connect(economy) as db:
            cursor = await db.execute("SELECT bank FROM economy WHERE user_id = ?", (interaction.user.id,))
            bank = await cursor.fetchone()
            if bank is None:
                await self.prime_db(interaction.user.id)
                bank = (0,)
            if amount > bank[0]:
                embed = discord.Embed(title="Withdrawal", description="You don't have enough coins in your bank to withdraw that much.", color=discord.Color.red())
                embed.set_thumbnail(url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed)
                return
            await db.execute("UPDATE economy SET balance = balance + ?, bank = bank - ? WHERE user_id = ?", (amount, amount, interaction.user.id))
            await db.commit()
            embed = discord.Embed(title="Withdrawal 🏧", description=f"You withdrew {amount} coins from your bank 🏦.", color=discord.Color.green())
            embed.add_field(name="New Wallet Balance:", value=f"{balance[0] + amount} coins 🪙")
            embed.add_field(name="New Bank Balance:", value=f"{balance[0] - amount} coins 💳")
            embed.set_thumbnail(url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="give", description="Give coins to another user")
    async def give(self, interaction: discord.Interaction, user: discord.Member, amount: int) -> None:
        async with aiosqlite.connect(economy) as db:
            cursor = await db.execute("SELECT balance FROM economy WHERE user_id = ?", (interaction.user.id,))
            balance = await cursor.fetchone()
            if balance is None:
                await self.prime_db(interaction.user.id)
                balance = (0,)
            if amount > balance[0]:
                embed = discord.Embed(title="Give", description="You don't have enough coins to give that much.", color=discord.Color.red())
                embed.set_thumbnail(url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed)
                return
            await db.execute("UPDATE economy SET balance = balance - ? WHERE user_id = ?", (amount, interaction.user.id))
            await db.execute("UPDATE economy SET balance = balance + ? WHERE user_id = ?", (amount, user.id))
            await db.commit()
            embed = discord.Embed(title="Give", description=f"You gave {amount} coins 🪙 to {user.mention}.", color=discord.Color.green())
            embed.add_field(name="New Wallet Balance:", value=f"{balance[0] - amount} coins 🪙")
            embed.set_thumbnail(url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)

    @balance.command(name="bank", description="Check your bank balance")
    async def bank(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(economy) as db:
            cursor = await db.execute("SELECT bank FROM economy WHERE user_id = ?", (interaction.user.id,))
            bank = await cursor.fetchone()
            if bank is None:
                await self.prime_db(interaction.user.id)
                bank = (0,)
            embed = discord.Embed(title="Bank Balance 🏦", description=f"Your bank balance is {bank[0]} coins 💳", color=discord.Color.green())
            embed.set_thumbnail(url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)

    @balance.command(name="leaderboard", description="Check the top 10 users with the most coins")
    async def leaderboard(self, interaction: discord.Interaction, balance: Literal["wallet", "bank"] = "wallet") -> None:
        async with aiosqlite.connect(economy) as db:
            if balance == "wallet":
                cursor = await db.execute("SELECT user_id, balance FROM economy ORDER BY balance DESC LIMIT 10")
            elif balance == "bank":
                cursor = await db.execute("SELECT user_id, bank FROM economy ORDER BY bank DESC LIMIT 10")
            rows = await cursor.fetchall()
            if not rows:
                embed = discord.Embed(title="Leaderboard", description="No users found", color=discord.Color.red())
                embed.set_thumbnail(url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed)
                return
            embed = discord.Embed(title="Leaderboard", description=f"Top 10 {balance} users", color=discord.Color.green())
            for i, row in enumerate(rows):
                user = self.bot.get_user(row[0])
                if user is None:
                    user = await self.bot.fetch_user(row[0])
                embed.add_field(name=f"{i+1}. {user.mention}", value=f"{row[1]} coins", inline=False)
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="shop", description="View the shop")
    async def shop(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title="Shop🛍️", description="Welcome to the shop! We are currently not open for buisiness while we stock items. We will keep you informed of our grand opening!", color=discord.Color.green())
        embed.add_field(name="Items🏷️", value="Coming soon! Stay tuned!")
        embed.set_thumbnail(url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot) -> None:
    await bot.add_cog(Economy(bot))