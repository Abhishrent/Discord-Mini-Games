import discord
from discord.ext import commands, tasks
import random
import asyncio
import time

#------------------Game Settings------------------#
CHECK_FREQUENCY = 1                               #
TIMEOUT_DURATION = 5                              #
#-------------------------------------------------#


class MemoryMatchingGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.emoji_list = ["🍎", "🍌", "🍒", "🍇", "🍉", "🍍", "🍓", "🍑", "🍊", "🍋", "🍏", "🥝"]
        self.game_timeout = TIMEOUT_DURATION
        self.check_game_timeouts.start()

    def cog_unload(self):
        self.check_game_timeouts.cancel()

    def shuffle_emoji_pairs(self):
        grid_size = 24
        unique_emoji_count = grid_size // 2

        if len(self.emoji_list) < unique_emoji_count:
            raise ValueError("Not enough unique emojis to fill the grid.")
        selected_emojis = random.sample(self.emoji_list, unique_emoji_count)
        emoji_pairs = selected_emojis * 2
        random.shuffle(emoji_pairs)
        emoji_pairs.append("🔹")

        return emoji_pairs

    def create_game_view(self, game):
        view = discord.ui.View()

        for i in range(25):
            if i == 24:
                button = discord.ui.Button(
                    label="Start Game" if not game["game_started"] else "Quit Game",
                    style=discord.ButtonStyle.danger if game["game_started"] else discord.ButtonStyle.primary,
                    custom_id="start_game"
                )
            elif i in game["matched"]:
                button = discord.ui.Button(
                    label=game["emoji_pairs"][i],
                    style=discord.ButtonStyle.success,
                    disabled=True,
                    custom_id=str(i)
                )
            elif i in game["revealed"]:
                button = discord.ui.Button(
                    label=game["emoji_pairs"][i],
                    style=discord.ButtonStyle.primary,
                    disabled=False,
                    custom_id=str(i)
                )
            else:
                button = discord.ui.Button(
                    label="❓",
                    style=discord.ButtonStyle.secondary,
                    custom_id=str(i),
                    disabled=not game["game_started"]
                )
            view.add_item(button)

        return view

    @commands.hybrid_command(name="memory", with_app_command=True)
    async def start_game(self, ctx):
        if ctx.channel.id in self.games:
            await ctx.send(embed=discord.Embed(
                title="Game Already Active",
                description="A memory matching game is already active in this channel! Please finish the current game before starting a new one.",
                color=discord.Color.red()
            ))
            return

        emoji_pairs = self.shuffle_emoji_pairs()
        game_state = {
            "emoji_pairs": emoji_pairs,
            "revealed": [],
            "matched": [],
            "current_turn": [],
            "owner": ctx.author.id,
            "start_time": None,
            "game_started": False,
            "is_processing": False,
            "last_interaction_time": time.time(),
            "message_id": None
        }

        embed = discord.Embed(
            title="Memory Matching Game Started!",
            description="",
            color=discord.Color.green()
        )
        embed.add_field(
            name="How to Play:",
            value="Click on two blocks to reveal the emojis. \nIf they match, they stay revealed.\nFind all the matches in the least time possible (shown at the end upon completion)",
            inline=False
        )

        message = await ctx.send(embed=embed, view=self.create_game_view(game_state))
        game_state["message_id"] = message.id
        self.games[ctx.channel.id] = game_state

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.user.bot:
            return

        game = self.games.get(interaction.channel.id)
        if not game:
            return
        
        if interaction.user.id != game["owner"]:
            await interaction.response.send_message(embed=discord.Embed(
                title="Not Your Game!",
                description="Only the person who started the game can play it! Start your own game using the `/memory` command.",
                color=discord.Color.red()
            ), ephemeral=True)
            return

        game['last_interaction_time'] = time.time()
        custom_id = interaction.data.get("custom_id")
        if not custom_id:
            return

        if custom_id == "start_game":
            if not game["game_started"]:
                game["game_started"] = True
                game["start_time"] = time.time()
                game["is_processing"] = False
                await interaction.response.edit_message(
                    content="The game has started! Enjoy!", 
                    view=self.create_game_view(game)
                )
            else:
                await interaction.response.edit_message(
                    content=None, 
                    embed=discord.Embed(
                        title="Game Quit",
                        description="The memory game has been quit.",
                        color=discord.Color.red()
                    ), 
                    view=None
                )
                del self.games[interaction.channel.id]
            return

        if not game["game_started"]:
            await interaction.response.send_message(
                "The game hasn't started yet. Press 'Start Game' to begin!", 
                ephemeral=True
            )
            return

        if game["is_processing"]:
            await interaction.response.send_message(
                "Please wait, the game is processing the previous move.", 
                ephemeral=True
            )
            return

        button_index = int(custom_id)
        if button_index in game["matched"] or button_index in game["current_turn"]:
            await interaction.response.send_message(
                "This button is already revealed or matched!", 
                ephemeral=True
            )
            return

        game["is_processing"] = True

        try:
            game["revealed"].append(button_index)
            game["current_turn"].append(button_index)
            await interaction.response.edit_message(view=self.create_game_view(game))

            if len(game["current_turn"]) == 2:
                await asyncio.sleep(0.3)

                first_index, second_index = game["current_turn"]
                if game["emoji_pairs"][first_index] == game["emoji_pairs"][second_index]:
                    game["matched"].extend([first_index, second_index])
                else:
                    game["revealed"] = [idx for idx in game["revealed"] if idx not in game["current_turn"]]

                game["current_turn"] = []
                await interaction.message.edit(view=self.create_game_view(game))

                if len(game["matched"]) == len(game["emoji_pairs"]) - 1:
                    elapsed_time = time.time() - game["start_time"]
                    minutes, seconds = divmod(int(elapsed_time), 60)
                    time_display = f"{minutes:02}:{seconds:02}"

                    channel = self.bot.get_channel(interaction.channel_id)
                    message = await channel.fetch_message(game["message_id"])
                    await message.edit(embed=discord.Embed(
                        title="Game Over",
                        description=f"🎉 {interaction.user.mention} found all pairs! The game is over.\n\nTotal Time: {time_display}",
                        color=discord.Color.green()
                    ), view=None)
                    del self.games[interaction.channel.id]

        except Exception as e:
            print(f"Error in game interaction: {e}")
        finally:
            game["is_processing"] = False

    @tasks.loop(seconds=CHECK_FREQUENCY)
    async def check_game_timeouts(self):
        current_time = time.time()
        channels_to_remove = []

        for channel_id, game in self.games.items():
            if (current_time - game["last_interaction_time"]) > self.game_timeout:
                try:
                    channel = self.bot.get_channel(channel_id)
                    message = await channel.fetch_message(game["message_id"])
                    await message.edit(embed=discord.Embed(
                        title="Game Timed Out",
                        description=f"Hey {self.bot.get_user(game['owner']).mention}! A good programmer never forgets to deallocate system resources after use and this timeout ensures that ;)\n Creating a game uses memory, quitting one frees the memory.\n So don't forget to hit the `quit` button if you're leaving!",
                        color=discord.Color.red()
                    ), view=None)
                except Exception as e:
                    print(f"Error in timeout handling for channel {channel_id}: {e}")
                finally:
                    channels_to_remove.append(channel_id)

        for channel_id in channels_to_remove:
            del self.games[channel_id]

    @check_game_timeouts.before_loop
    async def before_check_game_timeouts(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(MemoryMatchingGame(bot))