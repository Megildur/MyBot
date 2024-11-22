import discord
from discord.ext import commands
import random
from discord.ui import UserSelect
from typing import Any

class TicTacToe(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def tttstart(self, interaction, opponent) -> None:
        if opponent == interaction.user:
            await interaction.response.send_message("You can't challenge yourself!", ephemeral=True)
            return
        elif opponent.bot:
            await interaction.response.send_message("You can't challenge a bot!", ephemeral=True)
            return
        else:
            embed = discord.Embed(title="Tic-Tac-Toe", description=f"{interaction.user.mention} would like to challenge you to a game of tic-tac-toe! Do you accept?", color=0x34C759)
            view = TicTacToeViewAccept(interaction.user, opponent)
            await interaction.response.send_message(f"{opponent.mention}", embed=embed, view=view)

class TicTacToeViewAccept(discord.ui.View):
    def __init__(self, user, opponent) -> None:
        super().__init__(timeout=None)
        self.user = user
        self.opponent = opponent
        self.turn = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.user:
            await interaction.response.send_message("You cannot play against yourself.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="accept_ttt", emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.turn = random.choice([self.user, self.opponent])
        if self.turn == self.user:
            turn1 = self.user
            turn2 = self.opponent
        else:
            turn1 = self.opponent
            turn2 = self.user
        embed = discord.Embed(title="Tic-Tac-Toe", description=f"{self.opponent.mention} has accepted your challenge to a game of tic-tac-toe! Let the game begin!", color=discord.Color.green())
        embed.add_field(name="Instructions", value="To make a move, click on the corresponding square. The first player to get tree in a row wins!")
        embed.add_field(name="Player Turn", value=f"{self.turn.mention}'s turn")
        view = TicTacToeView(turn1, turn2, self.turn, self.opponent)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, custom_id= "decline_ttt", emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(title="Tic-Tac-Toe", description=f"{self.opponent.mention} has declined your challenge to a game of tic-tac-toe.", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=None)

class TicTacToeView(discord.ui.View):
    def __init__(self, user, opponent, turn, turn1) -> None:
        super().__init__(timeout=None)
        self.user = user
        self.opponent = opponent
        self.turn = turn
        self.board = ["1", "2", "3", "4", "5", "6", "7" ,"8", "9"]
        self.winner = None
        self.turn1 = turn1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.turn.id:
            await interaction.response.send_message("It's not your turn.", ephemeral=True)
            return False
        return True

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="ttt_0", row=0, emoji="<:ttt:1309506483230085143>")
    async def ttt_0(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.update_board(interaction, button, "0")

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="ttt_1", row=0, emoji="<:ttt:1309506483230085143>")
    async def ttt_1(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.update_board(interaction, button, "1")

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="ttt_2", row=0, emoji="<:ttt:1309506483230085143>")
    async def ttt_2(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.update_board(interaction, button, "2")

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="ttt_3", row=1, emoji="<:ttt:1309506483230085143>")
    async def ttt_3(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.update_board(interaction, button, "3")
                       
    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="ttt_4", row=1, emoji="<:ttt:1309506483230085143>")
    async def ttt_4(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.update_board(interaction, button, "4")
                       
    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="ttt_5", row=1, emoji="<:ttt:1309506483230085143>")
    async def ttt_5(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.update_board(interaction, button, "5")

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="ttt_6", row=2, emoji="<:ttt:1309506483230085143>")
    async def ttt_6(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.update_board(interaction, button, "6")

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="ttt_7", row=2, emoji="<:ttt:1309506483230085143>")
    async def ttt_7(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.update_board(interaction, button, "7")

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="ttt_8", row=2, emoji="<:ttt:1309506483230085143>")
    async def ttt_8(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.update_board(interaction, button, "8")

    async def update_board(self, interaction: discord.Interaction, button: discord.ui.Button, board_index: str) -> None:
        if self.winner != None:
            await interaction.response.send_message("The game has already ended!", ephemeral=True)
            return
        symbol = "❌" if self.turn.id == self.user.id else "⭕"
        button.emoji = symbol
        button.disabled = True
        self.board[int(board_index)] = symbol
        self.turn = self.opponent if self.turn == self.user else self.user
        await self.check_winner(interaction, symbol)

    async def check_winner(self, interaction: discord.Interaction, symbol: str) -> None:
        if await self.check_win():
            if symbol == "❌":
                self.winner = symbol
                embed = discord.Embed(title="Tic-Tac-Toe", description=f"{self.user.mention} has won the game of tic-tac-toe!", color=0x34C759)
                await interaction.response.edit_message(view=self, embed=embed)
                replay = discord.Embed(title="Tic-Tac-Toe", description="Would you like to play again?", color=0x34C759)
                await interaction.followup.send(view=TttPlayAgainView(), embed=replay)
            elif symbol == "⭕":
                self.winner = symbol
                embed = discord.Embed(title="Tic-Tac-Toe", description=f"{self.opponent.mention} has won the game of tic-tac-toe!", color=0x34C759)
                await interaction.response.edit_message(view=self, embed=embed)
                replay = discord.Embed(title="Tic-Tac-Toe", description="Would you like to play again?", color=0x34C759)
                await interaction.followup.send(view=TttPlayAgainView(), embed=replay)
        elif await self.check_tie():
            embed = discord.Embed(title="Tic-Tac-Toe", description="The game of tic-tac-toe has ended in a tie!", color=0x34C759)
            await interaction.response.edit_message(view=self, embed=embed)
            replay = discord.Embed(title="Tic-Tac-Toe", description="Would you like to play again?", color=0x34C759)
            await interaction.followup.send(view=TttPlayAgainView(), embed=replay)
        else:
            embed = discord.Embed(title="Tic-Tac-Toe", description=f"{self.turn1.mention} has accepted your challenge to a game of tic-tac-toe! Let the game begin!", color=0x34C759)
            embed.add_field(name="Instructions", value="To make a move, click on the corresponding square. The first player to get three in a row wins!")
            embed.add_field(name="Player Turn", value=f"{self.turn.mention}'s turn")
            await interaction.response.edit_message(view=self, embed=embed)

    async def check_win(self) -> bool:
        board = self.board
        if await self.check_rows(board):
            return True
        if await self.check_columns(board):
            return True
        if await self.check_diagonals(board):
            return True
        return False

    async def check_tie(self) -> bool:
        return all(cell == "❌" or cell == "⭕" for cell in self.board)
        
    async def check_rows(self, board) -> bool:
        for i in range(0, 7, 3):
            if board[i] == board[i + 1] == board[i + 2] and board[i] is not None:
                return True
        return False
        
    async def check_columns(self, board) -> bool:
        for i in range(0, 3):
            if board[i] == board[i + 3] == board[i + 6] and board[i] is not None:
                return True
        return False
        
    async def check_diagonals(self, board) -> bool:
        if board[0] == board[4] == board[8] and board[0] is not None:
            return True
        if board[2] == board[4] == board[6] and board[2] is not None:
            return True
        return False

class TttPlayAgainView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
 
    @discord.ui.button(label="New Game",emoji="➕", style=discord.ButtonStyle.green, custom_id="new_game_ttt")
    async def new_game(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        message = await interaction.original_response()
        embed = discord.Embed(title="Tic-Tac-Toe", description="Who would you like to challenge?")
        await interaction.followup.send(view=NewGameView(interaction.user, message), embed=embed, ephemeral=True)

class NewGameView(discord.ui.View):
    def __init__(self, user, message) -> None:
        super().__init__(timeout=None)
        self.user = user
        self.message = message
        
    @discord.ui.select(cls=UserSelect, placeholder="Select a user to challenge", min_values=1, max_values=1, custom_id="challenge_ttt")
    async def select_user(self, interaction: discord.Interaction, select: UserSelect) -> Any:
        if select.values[0].id == interaction.user.id:
            await interaction.response.send_message("You cannot challenge yourself.", ephemeral=True)
            return
        if select.values[0].bot:
            await interaction.response.send_message("You cannot challenge a bot.", ephemeral=True)
            return
        embed = discord.Embed(title="Tic-Tac-Toe", description=f"{interaction.user.mention} would like to challenge you to a game of tic-tac-toe! Do you accept?", color=0x34C759)
        await self.message.delete()
        await interaction.response.send_message(f'{select.values[0].mention}', embed=embed, view=TicTacToeViewAccept(interaction.user, select.values[0]))

async def setup(bot) -> None:
    await bot.add_cog(TicTacToe(bot))
    bot.add_view(TttPlayAgainView())
    print("TicTacToe cog loaded")