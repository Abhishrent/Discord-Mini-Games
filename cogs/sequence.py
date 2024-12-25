import discord
from discord.ext import commands, tasks
import random
import asyncio
import time

#---------------------------------Game Settings--------------------------------------#
TIMEOUT_DURATION = 2*60                                                              #
CHECK_FREQUENCY = 10                                                                 #
HIGHLIGHT_TIME = 0.5                                                                 #
#------------------------------------------------------------------------------------#

class SequenceMemoryGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.game_timeout = TIMEOUT_DURATION
        self.check_game_timeouts.start()

    def cog_unload(self):
        self.check_game_timeouts.cancel()

    def create_button(self, index, game_state, highlight=False):
        """Helper method to create a button with consistent styling."""
        if index == 24:  # Start/Quit button
            return discord.ui.Button(
                label="Start Game" if not game_state["game_started"] else "Quit Game",
                style=discord.ButtonStyle.primary if not game_state["game_started"] else discord.ButtonStyle.danger,
                custom_id=f"button_{index}"
            )
        
        return discord.ui.Button(
            label="\u200b",
            style=discord.ButtonStyle.success if highlight else discord.ButtonStyle.secondary,
            custom_id=f"button_{index}",
            disabled=not game_state["game_started"] or game_state["showing_sequence"] or highlight
        )

    def create_game_view(self, game_state, highlight_index=None):
        """Create a new view with buttons based on the current game state."""
        view = discord.ui.View()
        buttons = []

        for i in range(25):
            button = self.create_button(i, game_state, highlight_index == i)
            buttons.append(button)
            view.add_item(button)

        return view, buttons

    def create_embed(self, title, description, color=discord.Color.blue()):
        """Helper method to create consistently styled embeds."""
        return discord.Embed(title=title, description=description, color=color)

    @commands.hybrid_command(name="sequence", with_app_command=True)
    async def start_game(self, ctx):
        """Start a new sequence memory game."""
        if ctx.channel.id in self.games:
            await ctx.send("A game is already active in this channel!")
            return

        game_state = {
            "owner": ctx.author.id,
            "game_started": False,
            "current_sequence": [],
            "player_sequence": [],
            "round": 1,
            "showing_sequence": False,
            "last_interaction_time": time.time(),
            "message": None,
            "is_quitting": False
        }

        view, buttons = self.create_game_view(game_state)
        game_state["view"] = view
        game_state["buttons"] = buttons

        embed = self.create_embed(
            "Sequence Memory Game",
            "Watch the sequence of buttons that light up and repeat it!\nPress Start Game to begin."
        )
        
        message = await ctx.send(embed=embed, view=view)
        game_state["message"] = message
        self.games[ctx.channel.id] = game_state

    async def show_sequence(self, game):
        #Show the sequence to the player
        game["showing_sequence"] = True
        await game["message"].edit(view=self.create_game_view(game)[0])

        last_highlighted = None  # Track the last highlighted button

        for button_index in game["current_sequence"]:
            if game["is_quitting"]:
                return

            # Reset the timeout timer when highlighting a button
            game["last_interaction_time"] = time.time()
            
            # Ensure the same button is not highlighted twice in a row
            if button_index == last_highlighted:
                continue

            view, _ = self.create_game_view(game, highlight_index=button_index)
            await game["message"].edit(view=view)
            last_highlighted = button_index  # Update last highlighted button
            await asyncio.sleep(HIGHLIGHT_TIME)

        if not game["is_quitting"]:
            game["showing_sequence"] = False
            await game["message"].edit(view=self.create_game_view(game)[0])

    async def start_new_round(self, game):
        """Start a new round by adding to the sequence."""
        game["current_sequence"].append(random.randint(0, 23))
        game["player_sequence"] = []
        
        await game["message"].edit(
            embed=self.create_embed(f"Round {game['round']}", "Watch the sequence carefully!")
        )
        await self.show_sequence(game)
        
        if not game["is_quitting"]:
            await game["message"].edit(
                embed=self.create_embed(f"Round {game['round']}", "Now repeat the sequence!")
            )

    async def handle_game_end(self, game, interaction, reason, color=discord.Color.red()):
        """Helper method to handle game ending scenarios."""
        embed = self.create_embed("Game Over", reason, color)
        await interaction.response.edit_message(embed=embed, view=None)
        del self.games[interaction.channel.id]

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.message:
            return

        game = self.games.get(interaction.channel.id)
        if not game:
            return

        if interaction.user.id != game["owner"]:
            await interaction.response.send_message(
                embed=self.create_embed(
                    "Not Your Game!",
                    "Only the person who started the game can play it! Start your own game using the `/sequence` command.",
                    discord.Color.red()
                ),
                ephemeral=True
            )
            return

        game["last_interaction_time"] = time.time()
        button_id = interaction.data.get("custom_id")
        if not button_id:
            return

        button_index = int(button_id.split("_")[1])

        if button_index == 24:  # Start/Quit button
            if not game["game_started"]:
                game["game_started"] = True
                await interaction.response.defer()
                await self.start_new_round(game)
            else:
                game["is_quitting"] = True
                await self.handle_game_end(game, interaction, f"Game ended at Round {game['round']}")
            return

        if not game["game_started"] or game["showing_sequence"]:
            await interaction.response.send_message("Please wait...", ephemeral=True)
            return

        await interaction.response.defer()

        game["player_sequence"].append(button_index)
        current_index = len(game["player_sequence"]) - 1

        if game["player_sequence"][current_index] != game["current_sequence"][current_index]:
            await self.handle_game_end(game, interaction, f"Wrong sequence! You reached Round {game['round']}")
            return

        if len(game["player_sequence"]) == len(game["current_sequence"]):
            game["round"] += 1
            await asyncio.sleep(0.5)
            await self.start_new_round(game)

    @tasks.loop(seconds=CHECK_FREQUENCY)
    async def check_game_timeouts(self):
        current_time = time.time()
        for channel_id, game in list(self.games.items()):
            if current_time - game["last_interaction_time"] > self.game_timeout:
                try:
                    await game["message"].edit(
                        embed=self.create_embed(
                            "Game Timed Out",
                            "The game has been inactive for too long and has timed out.",
                            discord.Color.red()
                        ),
                        view=None
                    )
                except:
                    pass
                del self.games[channel_id]

    @check_game_timeouts.before_loop
    async def before_check_game_timeouts(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(SequenceMemoryGame(bot))