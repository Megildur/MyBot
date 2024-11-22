import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from typing import Optional, Literal
import random
from .fun_ext.ttt import TicTacToe
from .fun_ext.rps import RockPaperScissors

fortunes = [
    "*Be careful or you could fall for some tricks today.*",
    "*Bide your time, for success is near.*",
    "*Disbelief destroys the magic.*",
    "*Every flower blooms in its own sweet time.*",
    "*Feeding a cow with roses does not get extra appreciation.*",
    "*Good to begin well, better to end well.*",
    "*Help! I’m being held prisoner in a chinese bakery!*",
    "*It is better to deal with problems before they arise.*",
    "*Keep your face to the sunshine and you will never see shadows.*",
    "*Jump!*",
    "*Listen not to vain words of empty tongue.*",
    "*Miles are covered one step at a time.*",
    "*Now is the time to try something new.*",
    "*Opportunity seldom knocks twice.*",
    "*Practice makes permanent, not perfect.*",
    "*Pick battles big enough to matter, small enough to win.*",
    "*Remember the birthday but never the age.*",
    "*Someone you care about seeks reconciliation.*",
    "*Shit happens.*",
    "*Today, your mouth might be moving but no one is listening.*",
    "*The best people are molded of their faults.*",
    "*Uneasy lies the head that wears a crown.*",
    "*Virtue is its own reward.*",
    "*What’s that in your eye? Oh…it’s a sparkle.*",
    "*Xylophones are cool.*",
    "*You are almost there.*",
    "*You will take a chance in something in near future.*",
    "*Zeal without knowledge is a runaway horse*",
    "*To truly find yourself you should play hide and seek alone.*",
    "*The fortune you seek is in another cookie.*",
    "*Shame on you for thinking a cookie is psychic.*",
    "*This cookie fell on the ground.*",
    "*Error 404: Fortune not found.*",
    "*You aren't as good looking as your mom says you are.*",
    "*Don't play leap frog with a unicorn.*",
    "*Borrow money from pessimists, they won't expect it back*",
    "*You think it's a secret, but they know. They know.*",
    "*The GPS lady doesn't really care if you're lost*",
    "*Deez nuts*",
    "*Someone is looking up to you, don't let them down.*",
    "*run.*",
    "*No snowflake in an avalanche ever feels responsible.*",
    "*About time I got out of that cookie, thanks.*",
    "*Don't be afraid to take that big step.*",
    "*I cannot help you, for I am just a cookie.*",
    "*You will marry a professional athlete, if competitive eating can be considered a sport.*",
    "*Enjoy yourself while you can.*",
    "*Congrats you're not illiterate.*",
    "*I see money in your future.. it's not yours though.*",
    "*Three can keep a secret, if you get rid of two.*",
    "*Death.*",
    "*Avoid taking unnecessary gambles.*",
    "*Your efforts haven't gone unnoticed.*",
    "*This cookie is never gonna give you up, never gonna let you down.*",
    "*Catch on fire with enthusiasm and people will come from miles to watch you burn.*",
    "*Pigeon poop burns the retina for 13 hours. You will learn this the hard way.*",
    "*You are about to finish reading a fortune cookie.*",
    "*Be kind to pigeons if you want a statue of yourself one day.*",
    "*Your resemblance to a muppet will prevent the world from taking you seriously.*",
    "*Prepare for the unexpected.*",
    "*Pull your head out of your ass, then life won't be so shitty.*",
    "*Wouldn't it be ironic to die in the living room?*",
    "*If people are talking about you behind your back, just fart.*",
    "*Life doesn't get better by chance. It gets better by chance.*",
    "*Blessed are the children for they shall inherit the national debt.*",
    "*When in anger, sing the alphabet.*",
    "*It would be best to maintain a low profile for now.*",
    "*Winning doesn’t always mean being first, it means you’re doing better than you’ve done before.*",
    "*You’re braver than you believe, stronger than you seem, and smarter than you think.*",
    "*Keep your face to the sunshine and you cannot see a shadow.*",
    "*If you want the rainbow, you gotta put up with the rain.*",
    "*A truly happy person is one who can enjoy the scenery while on a detour.*",
    "*Limits, like fears, are often just an illusion.*",
    "*The more you dream, the farther you get.*",
    "*Do not be afraid of competition.*",
    "*An exciting opportunity lies ahead of you.*",
    "*Your ability to juggle many tasks will take you far.*",
    "*Beware of all enterprises that require new clothes.*",
    "*Be true to your work, your word, and your friend.*",
    "*Goodness is the only investment that never fails.*",
    "*Forget injuries but never forget kindnesses.*",
    "*It is easier to stay out than to get out.*",
    "*Attitude is a little thing that makes a big difference.*",
    "*Experience is the best teacher.*",
    "*Eat chocolate to have a sweeter life.*",
    "*The only way to have a friend is to be one.*",
    "*Dance as if no one is watching.*",
    "*Live this day as if it were your last, totally not a death threat.*",
    "*Bloom where you are planted.*",
    "*Real eyes realize real lies.*",
    "*He who throws dirt is losing ground.*",
    "*The one you love is closer than you think.*",
    "*Don’t hold onto things that require a tight grip.*",
    "*What good are wings, without the courage to fly?*",
    "*Get lost in the right direction.*",
    "*Soon you'll be sitting on top of the world.*",
    "*It's Britney, bitch.*",
    "*You can have your cake and eat it too.*",
    "*Your pet is planning to eat you.*",
    "*You're more likely to regret the things you didn't do rather than the things you did.*",
    "You're not illiterate, you're just not good at fortune cookies.",
    "*The best way to get started is to quit talking and begin doing.*",
    "*I'm not afraid of storms, for I am learning how to sail my ship.*",
    "The time is always right to do what is right."
]

responses = [
    'It is certain.',
    'It is decidedly so.',
    'Without a doubt.',
    'Yes - definitely.',  
    'You may rely on it.',       
    'As I see it, yes.',
    'Most likely.',
    'Outlook good.',
    'Yes.',
    'Signs point to yes.',
    'Reply hazy, try again.',
    'Ask again later.',
    'Better not tell you now.',
    'Cannot predict now.',
    'Concentrate and ask again.',
    'Don\'t count on it.',
    'My reply is no.',
    'My sources say no.',
    'Outlook not so good.',
    'Very doubtful.',
    'No.',
    'Maybe.',
    'I don\'t know.'
]

side_options=[
    discord.SelectOption(label="3", value="3"),
    discord.SelectOption(label="4", value="4"),
    discord.SelectOption(label="6", value="6"),
    discord.SelectOption(label="8", value="8"),
    discord.SelectOption(label="10", value="10"),
    discord.SelectOption(label="12", value="12"),
    discord.SelectOption(label="20", value="20"),
    discord.SelectOption(label="Percentage", value="100")
]

rolls_options=[
    discord.SelectOption(label="1", value="1"),
    discord.SelectOption(label="2", value="2"),
    discord.SelectOption(label="3", value="3"),
    discord.SelectOption(label="4", value="4"),
    discord.SelectOption(label="5", value="5"),
    discord.SelectOption(label="6", value="6"),
    discord.SelectOption(label="7", value="7"),
    discord.SelectOption(label="8", value="8"),
    discord.SelectOption(label="9", value="9"),
    discord.SelectOption(label="10", value="10"),
    discord.SelectOption(label="11", value="11"),
    discord.SelectOption(label="12", value="12"),
    discord.SelectOption(label="13", value="13"),
    discord.SelectOption(label="14", value="14"),
    discord.SelectOption(label="15", value="15"),
    discord.SelectOption(label="16", value="16"),
    discord.SelectOption(label="17", value="17"),
    discord.SelectOption(label="18", value="18"),
    discord.SelectOption(label="19", value="19"),
    discord.SelectOption(label="20", value="20")
]

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class Fun(commands.GroupCog, group_name='fun'):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    dice = app_commands.Group(name='dice', description='Rolls a dice')
            
    @app_commands.command(name="fortune", description="Get a fortune cookie")
    @app_commands.checks.cooldown(1, 43200, key=lambda i: i.user.id)
    async def fortune(self, interaction: discord.Interaction) -> None:
        await self.fortune_cookie(interaction)

    async def fortune_cookie(self, interaction) -> None:
        fortune = random.choice(fortunes)
        embed = discord.Embed(title=f"**{interaction.user.display_name}'s** fortune says…", description=fortune, color=0x00ff00)
        file = discord.File("data/images/fun/fortune.jpg", filename="fortune.jpg")
        embed.set_thumbnail(url="attachment://fortune.jpg")
        view = NextFortuneView(self.bot)
        await interaction.response.send_message(file=file, embed=embed, view=view)

    @app_commands.command(name="8ball", description="Ask the magic 8 ball a question")
    @app_commands.checks.cooldown(1, 30, key=lambda i: i.user.id)
    async def fun_eight_ball(self, interaction: discord.Interaction, question: str) -> None:
        await self.eight_ball_response(interaction, question)

    async def eight_ball_response(self, interaction: discord.Interaction, question: str) -> None:
        embed = discord.Embed(title="Magic 8 Ball", description=f"{interaction.user.display_name}'s Question: {question}", color=0x00ff00)
        embed.add_field(name=f"{interaction.user.display_name}'s Answer", value=random.choice(responses), inline=False)
        file = discord.File("data/images/fun/8ball.png", filename="8ball.png")
        embed.set_thumbnail(url="attachment://8ball.png")
        view = EightBallView(self.bot)

        await interaction.response.send_message(file=file, embed=embed, view=view)

    @app_commands.command(name="coinflip", description="Flips a coin")
    @app_commands.checks.cooldown(1, 30, key=lambda i: i.user.id)
    async def fun_coinflip(self, interaction: discord.Interaction) -> None:
        await self.coinflip(interaction)

    async def coinflip(self, interaction: discord.Interaction) -> None:
        choices = ['Heads', 'Tails']
        choice = random.choice(choices)

        embed = discord.Embed(title="Coin Flip", description=f"{interaction.user.display_name} flipped a coin and got {choice}!", color=0x00ff00)
        if choice == 'Heads':
            file = discord.File("data/images/fun/heads.png", filename="heads.png")
            embed.set_thumbnail(url="attachment://heads.png")
        else:
            file = discord.File("data/images/fun/tails.png", filename="tails.png")
            embed.set_thumbnail(url="attachment://tails.png")

        view = CoinFlipView(self.bot)

        await interaction.response.send_message(file=file, embed=embed, view=view)

    @dice.command(name="roll", description="Roll a dice. Rolls default to 1 when when not used")
    @app_commands.describe(sides="The number of sides on the dice", rolls="The number of dice to roll. Defaults to 1.")
    @app_commands.checks.cooldown(1, 30, key=lambda i: i.user.id)
    @app_commands.choices(
        sides = [
            app_commands.Choice(name="3", value=3),
            app_commands.Choice(name="4", value=4),
            app_commands.Choice(name="6", value=6),
            app_commands.Choice(name="8", value=8),
            app_commands.Choice(name="10", value=10),
            app_commands.Choice(name="12", value=12),
            app_commands.Choice(name="20", value=20),
            app_commands.Choice(name="Percentage", value=100)
        ]
    )
    async def fun_roll_dice(
        self, 
        interaction: discord.Interaction, 
        sides: Choice[int],
        rolls: Optional[Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]] = 1
    ) -> None:
        await self.roll(interaction, sides, rolls)
        
    async def roll(self, interaction: discord.Interaction, sides, rolls) -> None:
        try:
            choices = [random.randint(1, sides.value) for _ in range(rolls)]
        except AttributeError:
            choices = [random.randint(1, sides) for _ in range(rolls)]
        total = sum(choices)
        try:
            roll_sides = sides.value
        except AttributeError:
            roll_sides = sides
        if roll_sides == 100:
            embed = discord.Embed(title="Dice Roll", description=f"{interaction.user.display_name} is rolling a percentage...", color=0x00ff00)
            embed.add_field(name="Results", value=f"{'%, '.join(map(str, choices))}%", inline=False)
            file = discord.File("data/images/fun/d10.png", filename="d10.png")
            embed.set_thumbnail(url="attachment://d10.png")
            view = DiceRollAgainView(self.bot)
            await interaction.response.send_message(file=file, embed=embed, view=view)
            return
        else:
            embed = discord.Embed(title="Dice Roll", description=f"{interaction.user.display_name} is rolling {rolls}d{roll_sides}...", color=0x00ff00)
            embed.add_field(name="Results", value=f"{', '.join(map(str, choices))}", inline=False)
            if rolls >= 2:
                embed.add_field(name=f"{interaction.user.display_name}\'s Total", value=f"That's a total of {total}!", inline=False)
            if roll_sides == 3:
                file = discord.File("data/images/fun/d6.png", filename="d6.png")
                embed.set_thumbnail(url="attachment://d6.png")
            elif roll_sides == 4:
                file = discord.File("data/images/fun/d4.png", filename="d4.png")
                embed.set_thumbnail(url="attachment://d4.png")
            elif roll_sides == 6:
                file = discord.File("data/images/fun/d6.png", filename="d6.png")
                embed.set_thumbnail(url="attachment://d6.png")
            elif roll_sides == 8:
                file = discord.File("data/images/fun/d8.png", filename="d8.png")
                embed.set_thumbnail(url="attachment://d8.png")
            elif roll_sides == 10:
                file = discord.File("data/images/fun/d10.png", filename="d10.png")
                embed.set_thumbnail(url="attachment://d10.png")
            elif roll_sides == 12:
                file = discord.File("data/images/fun/d12.png", filename="d12.png")
                embed.set_thumbnail(url="attachment://d12.png")
            elif roll_sides == 20:
                file = discord.File("data/images/fun/d20.png", filename="d20.png")
                embed.set_thumbnail(url="attachment://d20.png")
            view = DiceRollAgainView(self.bot)
            await interaction.response.send_message(file=file, embed=embed, view=view)

    @app_commands.command(name="tictactoe", description="Play a game of tic-tac-toe")
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)
    async def tictactoe(self, interaction: discord.Interaction, opponent: discord.Member | discord.User):
        await TicTacToe(self.bot).tttstart(interaction, opponent)

    @app_commands.command(name="rock_paper_scissors", description="Play a game of rock-paper-scissors!")
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)
    async def rps_self(self, interaction: discord.Interaction):
        await RockPaperScissors(self.bot).rpss(interaction)

class ButtonOnCooldown(commands.CommandError):
    def __init__(self, retry_after: float) -> None:
        self.retry_after = retry_after

def key(interaction: discord.Interaction) -> int:
    return interaction.user.id

global_cooldown_f = commands.CooldownMapping.from_cooldown(1, 43200, key)

global_cooldown_8 = commands.CooldownMapping.from_cooldown(1, 30, key)

global_cooldown_d = commands.CooldownMapping.from_cooldown(6, 30, key)

global_cooldown_da = commands.CooldownMapping.from_cooldown(6, 30, key)

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

class NextFortuneView(discord.ui.View):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

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
        label="Next Fortune", 
        custom_id="next_fortune",
        emoji="🔮",
        style=discord.ButtonStyle.primary
    )
    async def next_fortune(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled = True
        await Fun(self.bot).fortune_cookie(interaction)
        if interaction.message:
            try:
                await interaction.message.edit(view=self)
            except discord.errors.Forbidden:
                pass

class EightBallView(discord.ui.View):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        retry_after = global_cooldown_8.update_rate_limit(interaction)
        if retry_after:
            raise ButtonOnCooldown(retry_after)
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        if isinstance(error, ButtonOnCooldown):
            await error_handler(interaction, error)
        else:
            await super().on_error(interaction, error, item)

    @discord.ui.button(
        label="Ask Again", 
        custom_id="ask_again_ball",
        emoji="🎱",
        style=discord.ButtonStyle.primary
    )
    async def ask_again(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(AskAgainModal(self.bot, button, self))

class AskAgainModal(discord.ui.Modal, title="Ask Again"):
    def __init__(self, bot, button, view) -> None:
        super().__init__()
        self.bot = bot
        self.button = button
        self.view = view
        
    question = discord.ui.TextInput(
            label="Enter your question", 
        placeholder="What's your question?"
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.button.disabled = True
        await Fun(self.bot).eight_ball_response(interaction, self.question.value)
        if interaction.message:
            try:
                await interaction.message.edit(view=self.view)
            except discord.errors.Forbidden:
                pass

class CoinFlipView(discord.ui.View):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        retry_after = global_cooldown_8.update_rate_limit(interaction)
        if retry_after:
            raise ButtonOnCooldown(retry_after)
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        if isinstance(error, ButtonOnCooldown):
            await error_handler(interaction, error)
        else:
            await super().on_error(interaction, error, item)

    @discord.ui.button(
        label="Flip Again", 
        custom_id="flip_again_coin",
        emoji="🪙",
        style=discord.ButtonStyle.primary
    )
    async def flip_again(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled = True
        await Fun(self.bot).coinflip(interaction)
        if interaction.message:
            try:
                await interaction.message.edit(view=self)
            except discord.errors.Forbidden:
                pass

class DiceRollAgainView(discord.ui.View):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        retry_after = global_cooldown_da.update_rate_limit(interaction)
        if retry_after:
            raise ButtonOnCooldown(retry_after)
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        if isinstance(error, ButtonOnCooldown):
            await error_handler(interaction, error)
        else:
            await super().on_error(interaction, error, item)

    @discord.ui.button(
        label="Roll Again", 
        custom_id="roll_again_dice",
        emoji="🎲",
        style=discord.ButtonStyle.primary
    )
    async def roll_again(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled = True
        view = DiceRollView(self.bot)
        embed = discord.Embed(title="Dice Roll", description="Please make your selections and click the button below to roll the dice!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class DiceRollView(discord.ui.View):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.sides = 0
        self.rolls = 0

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        retry_after = global_cooldown_d.update_rate_limit(interaction)
        if retry_after:
            raise ButtonOnCooldown(retry_after)
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        if isinstance(error, ButtonOnCooldown):
            await error_handler(interaction, error)
        else:
            await super().on_error(interaction, error, item)
        
    @discord.ui.select(
        options=side_options, 
        row=0, 
        placeholder="Select the number of sides on the dice", 
        min_values=1, 
        max_values=1, 
        custom_id="dice_roll_sides"
    )
    async def dice_roll_sides(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        self.sides = int(select.values[0])
        await interaction.response.defer()

    @discord.ui.select(options=rolls_options, row=1, placeholder="Select the number of dice to roll (defaults to 1)", min_values=0, max_values=1, custom_id="dice_roll_rolls")
    async def dice_roll_rolls(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        self.rolls = int(select.values[0])
        await interaction.response.defer()

    @discord.ui.button(
        label="Reroll", 
        row=2,
        custom_id="reroll_simple_dice",
        emoji="🎲",
        style=discord.ButtonStyle.primary
        )
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled = True
        if self.sides == 0:
            await interaction.response.send_message("Please select the number of sides on the dice first.", ephemeral=True)
            return
        else:
            if self.rolls == 0:
                self.rolls = 1
            await Fun(self.bot).roll(interaction, self.sides, self.rolls)
            if interaction.message:
                try:
                    await interaction.message.edit(view=self)
                except discord.errors.Forbidden:
                    pass

async def setup(bot) -> None:
    await bot.add_cog(Fun(bot))
    bot.add_view(NextFortuneView(bot))
    bot.add_view(EightBallView(bot))
    bot.add_view(CoinFlipView(bot))
    bot.add_view(DiceRollView(bot))
    bot.add_view(DiceRollAgainView(bot))
    await bot.load_extension(f'bot.cogs.fun_ext.ttt')
    await bot.load_extension(f'bot.cogs.fun_ext.rps')