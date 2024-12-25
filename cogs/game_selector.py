import discord
from discord.ext import commands
from discord import app_commands

class GameSelector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="game", description="Select a game to play")
    @app_commands.describe(title="Supports single player modes only. Use respective commands for multiplayer.")
    @app_commands.choices(title=[
        app_commands.Choice(name="Tic-Tac-Toe", value="tictactoe"),
        app_commands.Choice(name="Wordle", value="wordle"),
        app_commands.Choice(name="Memory Blocks", value="memory"),
        app_commands.Choice(name="Sequence Memoriser", value="sequence")
    ])
    async def game_selector(self, ctx, *, title: str):
        # Normalize title for case-insensitive matching
        title = title.lower()

        # Start the appropriate game based on selection
        if title in ['tictactoe', 'ttt', 'tic-tac-toe']:
            # Use the existing Tic-Tac-Toe start game method
            ttt_cog = self.bot.get_cog('TicTacToeGame')
            if ttt_cog:
                await ttt_cog.start_game(ctx)
            else:
                await ctx.send("Tic-Tac-Toe game is not loaded.")

        elif title in ['wordle', 'word']:
            # Use the existing Wordle start game method
            wordle_cog = self.bot.get_cog('WordleGame')
            if wordle_cog:
                await wordle_cog.start_game(ctx)
            else:
                await ctx.send("Wordle game is not loaded.")

        elif title in ['memory']:
            # Use the existing Wordle start game method
            memory_cog = self.bot.get_cog('MemoryMatchingGame')
            if memory_cog:
                await memory_cog.start_game(ctx)
            else:
                await ctx.send("Memory game is not loaded.")


        elif title in ['sequence']:
            # Use the existing Wordle start game method
            memory_cog = self.bot.get_cog('SequenceMemoryGame')
            if memory_cog:
                await memory_cog.start_game(ctx)
            else:
                await ctx.send("Sequence game is not loaded.")

        else:
            # Invalid game selection
            await ctx.send("Please choose between Tic-Tac-Toe or Wordle.")

async def setup(bot):
    await bot.add_cog(GameSelector(bot))
