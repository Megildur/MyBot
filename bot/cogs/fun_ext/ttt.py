import discord
from discord.ext import commands
import random
from discord.ui import UserSelect

games = {}

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("TicTacToe cog loaded")

    async def tttstart(self, interaction, opponent):
        if opponent == interaction.user:
            await interaction.response.send_message("You can't challenge yourself!", ephemeral=True)
            return
        elif opponent.bot:
            await interaction.response.send_message("You can't challenge a bot!", ephemeral=True)
            return
        else:
            embed = discord.Embed(title="Tic-Tac-Toe", description=f"{interaction.user.mention} would like to challenge you to a game of tic-tac-toe! Do you accept?", color=0x34C759)
            view = TicTacToeViewAccept(interaction.user, opponent)
            message = await interaction.response.send_message(f"{opponent.mention}", embed=embed, view=view)

class TicTacToeViewAccept(discord.ui.View):
    def __init__(self, user, opponent):
        super().__init__(timeout=None)
        self.user = user
        self.opponent = opponent
        self.turn = user

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user == self.user:
            await interaction.response.send_message("You cannot play against yourself.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="accept_ttt", emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        message = await interaction.original_response()
        game_id = message.id
        turn1 = random.choice([self.user, self.opponent])
        games[game_id] = {
            'user': self.user,
            'opponent': self.opponent,
            'turn': turn1,
            'board': [None for _ in range(9)],
            'winner': None
        }
        embed = discord.Embed(title="Tic-Tac-Toe", description=f"{self.opponent.mention} has accepted your challenge to a game of tic-tac-toe! Let the game begin!", color=0x34C759)
        embed.add_field(name="Instructions", value="To make a move, click on the corresponding square. The first player to get tree in a row wins!")
        embed.add_field(name="Player Turn", value=f"{turn1.mention}'s turn")
        view = TicTacToeView(game_id)
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, custom_id= "decline_ttt", emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Tic-Tac-Toe", description=f"{self.opponent.mention} has declined your challenge to a game of tic-tac-toe.", color=0x34C759)
        await interaction.response.edit_message(embed=embed, view=None)

class TicTacToeView(discord.ui.View):
    def __init__(self, game_id):
        super().__init__(timeout=None)
        self.game_id = game_id

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.grey, custom_id="ttt_0", row=0)
    async def ttt_0(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        message = await interaction.original_response()
        self.game_id = message.id
        await self.update_board(interaction, button, 0)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.grey, custom_id="ttt_1", row=0)
    async def ttt_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        message = await interaction.original_response()
        self.game_id = message.id
        await self.update_board(interaction, button, 1)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.grey, custom_id="ttt_2", row=0)
    async def ttt_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        message = await interaction.original_response()
        self.game_id = message.id
        await self.update_board(interaction, button, 2)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.grey, custom_id="ttt_3", row=1)
    async def ttt_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        message = await interaction.original_response()
        self.game_id = message.id
        await self.update_board(interaction, button, 3)
                       
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.grey, custom_id="ttt_4", row=1)
    async def ttt_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        message = await interaction.original_response()
        self.game_id = message.id
        await self.update_board(interaction, button, 4)
                       
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.grey, custom_id="ttt_5", row=1)
    async def ttt_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        message = await interaction.original_response()
        self.game_id = message.id
        await self.update_board(interaction, button, 5)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.grey, custom_id="ttt_6", row=2)
    async def ttt_6(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        message = await interaction.original_response()
        self.game_id = message.id
        await self.update_board(interaction, button, 6)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.grey, custom_id="ttt_7", row=2)
    async def ttt_7(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        message = await interaction.original_response()
        self.game_id = message.id
        await self.update_board(interaction, button, 7)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.grey, custom_id="ttt_8", row=2)
    async def ttt_8(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        message = await interaction.original_response()
        await self.update_board(interaction, button, 8)

    async def update_board(self, interaction: discord.Interaction, button: discord.ui.Button, board_index: int):
        if button.label == "\u200b":
            if games[self.game_id]['winner'] is not None:
                await interaction.followup.send("The game has already ended.", ephemeral=True)
                return
            if interaction.user.id != games[self.game_id]['turn'].id:
                await interaction.followup.send("It's not your turn.", ephemeral=True)
                return
            symbol = "X" if games[self.game_id]['turn'].id == games[self.game_id]['user'].id else "O"
            button.label = symbol
            if games[self.game_id]['turn'] == games[self.game_id]['user']:
                button.style = discord.ButtonStyle.green
            else:
                button.style = discord.ButtonStyle.red
            # Update the game board
            games[self.game_id]['board'][board_index] = symbol
            # Switch the turn
            games[self.game_id]['turn'] = games[self.game_id]['opponent'] if games[self.game_id]['turn'] == games[self.game_id]['user'] else games[self.game_id]['user']
            await self.check_winner(interaction, symbol)
        else:
            await interaction.followup.send("That square is already taken.", ephemeral=True)

    async def check_winner(self, interaction: discord.Interaction, symbol: str):
        if await self.check_win():
            if symbol == "X":
                games[self.game_id]['winner'] = symbol
                embed = discord.Embed(title="Tic-Tac-Toe", description=f"{games[self.game_id]['user'].mention} has won the game of tic-tac-toe!", color=0x34C759)
                await interaction.edit_original_response(view=self, embed=embed)
                replay = discord.Embed(title="Tic-Tac-Toe", description="Would you like to play again?", color=0x34C759)
                await interaction.followup.send(view=TttPlayAgainView(), embed=replay)
            elif symbol == "O":
                games[self.game_id]['winner'] = symbol
                embed = discord.Embed(title="Tic-Tac-Toe", description=f"{games[self.game_id]['opponent'].mention} has won the game of tic-tac-toe!", color=0x34C759)
                await interaction.edit_original_response(view=self, embed=embed)
                replay = discord.Embed(title="Tic-Tac-Toe", description="Would you like to play again?", color=0x34C759)
                await interaction.followup.send(view=TttPlayAgainView(), embed=replay)
        elif await self.check_tie():
            embed = discord.Embed(title="Tic-Tac-Toe", description="The game of tic-tac-toe has ended in a tie!", color=0x34C759)
            await interaction.edit_original_response(view=self, embed=embed)
            replay = discord.Embed(title="Tic-Tac-Toe", description="Would you like to play again?", color=0x34C759)
            await interaction.followup.send(view=TttPlayAgainView(), embed=replay)
        else:
            embed = discord.Embed(title="Tic-Tac-Toe", description=f"{games[self.game_id]['opponent'].mention} has accepted your challenge to a game of tic-tac-toe! Let the game begin!", color=0x34C759)
            embed.add_field(name="Instructions", value="To make a move, click on the corresponding square. The first player to get three in a row wins!")
            embed.add_field(name="Player Turn", value=f"{games[self.game_id]['turn'].mention}'s turn")
            await interaction.edit_original_response(view=self, embed=embed)

    async def check_win(self):
        board = games[self.game_id]['board']
        # Check rows
        if await self.check_rows(board):
            return True
        # Check columns
        if await self.check_columns(board):
            return True
        # Check diagonals
        if await self.check_diagonals(board):
            return True
        return False  # No win condition

    async def check_tie(self):
        
        return all(cell is not None for cell in games[self.game_id]['board'])
        
    async def check_rows(self, board):
        # Check all rows
        for i in range(0, 7, 3):
            if board[i] == board[i + 1] == board[i + 2] and board[i] is not None:
                return True
        return False
    async def check_columns(self, board):
        # Check all columns
        for i in range(0, 3):
            if board[i] == board[i + 3] == board[i + 6] and board[i] is not None:
                return True
        return False
    async def check_diagonals(self, board):
        # Check diagonals
        if board[0] == board[4] == board[8] and board[0] is not None:
            return True
        if board[2] == board[4] == board[6] and board[2] is not None:
            return True
        return False

class TttPlayAgainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="New Game",emoji="➕", style=discord.ButtonStyle.green, custom_id="new_game_ttt")
    async def new_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.response.defer()
        await interaction.edit_original_response(view=self)
        message = await interaction.original_response()
        messages[interaction.user.id] = message
        embed = discord.Embed(title="Tic-Tac-Toe", description="Who would you like to challenge?")
        await interaction.followup.send(view=NewGameView(interaction.user, button), embed=embed, ephemeral=True)

class NewGameView(discord.ui.View):
    def __init__(self, user, button):
        super().__init__(timeout=None)
        self.user = user
        self.button = button
    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Select a user to challenge", min_values=1, max_values=1, custom_id="challenge_ttt")
    async def select_user(self, interaction: discord.Interaction, select: UserSelect):
        if select.values[0].id == interaction.user.id:
            await interaction.response.send_message("You cannot challenge yourself.", ephemeral=True)
            return
        if select.values[0].bot:
            await interaction.response.send_message("You cannot challenge a bot.", ephemeral=True)
            return
        message = messages[interaction.user.id]
        await message.delete()
        embed = discord.Embed(title="Tic-Tac-Toe", description=f"{interaction.user.mention} would like to challenge you to a game of tic-tac-toe! Do you accept?", color=0x34C759)
        await interaction.response.send_message(f'{select.values[0].mention}', embed=embed, view=TicTacToeViewAccept(interaction.user, select.values[0]))

async def setup(bot):
    await bot.add_cog(TicTacToe(bot))
    bot.add_view(TttPlayAgainView()) 