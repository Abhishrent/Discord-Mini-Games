import discord
from discord.ext import commands, tasks
import random
import time

#---------------------------------Game Settings--------------------------------------#
CHECK_FREQUENCY = 10  # checks for timeout every n seconds                           #
TIMEOUT_DURATION = 2*60  # n*60 => game times out in n minutes                       #
#------------------------------------------------------------------------------------#

class WordleGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.word_list = self.load_words('words.txt')
        self.game_timeout = TIMEOUT_DURATION
        self.check_game_timeouts.start()

    def cog_unload(self):
        self.check_game_timeouts.cancel()

    def load_words(self, filename):
        try:
            with open(filename, "r") as file:
                return [line.strip().upper() for line in file if line.strip()]
        except FileNotFoundError:
            print(f"Error: {filename} not found!")
            return []

    @commands.hybrid_command(name="wordle", with_app_command=True)
    async def start_game(self, ctx, word: str = None, hint: str = None):
        if ctx.channel.id in self.games:
            await ctx.send(embed=discord.Embed(
                title="Game Already Active",
                description="A Wordle game is already active in this channel! Please finish the current game before starting a new one.",
                color=discord.Color.red()
            ))
            return
        
        if word:
            target_word = word.upper()
            if len(target_word) != 5 or not target_word.isalpha():
                await ctx.send(embed=discord.Embed(
                    title="Invalid Word",
                    description="The word must be exactly 5 letters long and contain only letters.",
                    color=discord.Color.red()
                ))
                return
        else:
            target_word = random.choice(self.word_list)

        view = discord.ui.View()
        for _ in range(25):
            button = discord.ui.Button(label="\u200b", style=discord.ButtonStyle.secondary)
            view.add_item(button)
        
        embed = discord.Embed(
            title="Wordle Game Started!",
            description="Send your guesses (5-letter words). Good luck!",
            color=discord.Color.green()
        )
        embed.add_field(name="How to Play", value="Type a 5-letter word to guess the target word.", inline=False)
        
        if hint:
            embed.add_field(name="Hint", value=hint, inline=False)

        message = await ctx.send(embed=embed, view=view)
        self.games[ctx.channel.id] = {
            "target_word": target_word,
            "current_row": 0,
            "message_id": message.id,
            "owner": ctx.author.id,
            "hint": hint,
            "last_interaction_time": time.time()
        }

    @tasks.loop(seconds=CHECK_FREQUENCY)
    async def check_game_timeouts(self):
        current_time = time.time()
        channels_to_remove = []

        for channel_id, game in self.games.items():
            if (current_time - game["last_interaction_time"]) > self.game_timeout:
                try:
                    channel = self.bot.get_channel(channel_id)
                    message = await channel.fetch_message(game["message_id"])
                    timeout_embed = discord.Embed(
                        title="Game Timed Out",
                        description=f"Hey {self.bot.get_user(game['owner']).mention}! The game has timed out due to inactivity.\nThe word was **{game['target_word']}**.\nStart a new game with `/wordle`!",
                        color=discord.Color.red()
                    )
                    await message.edit(embed=timeout_embed, view=None)
                except Exception as e:
                    print(f"Error in timeout handling for channel {channel_id}: {e}")
                finally:
                    channels_to_remove.append(channel_id)

        for channel_id in channels_to_remove:
            del self.games[channel_id]

    @check_game_timeouts.before_loop
    async def before_check_game_timeouts(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name="quit", with_app_command=True)
    async def quit_game(self, ctx):
        if ctx.channel.id not in self.games:
            await ctx.send(embed=discord.Embed(
                title="No Active Game",
                description="There is no active Wordle game in this channel to quit.",
                color=discord.Color.red()
            ))
            return
        
        game = self.games[ctx.channel.id]
        if game["owner"] != ctx.author.id:
            await ctx.send(embed=discord.Embed(
                title="Permission Denied",
                description="Only the game owner can quit the game.",
                color=discord.Color.red()
            ))
            return

        del self.games[ctx.channel.id]
        await ctx.send(embed=discord.Embed(
            title="Game Quit",
            description="The Wordle game has been quit. Feel free to start a new game with `/wordle`.",
            color=discord.Color.blue()
        ))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if message.channel.id not in self.games:
            return

        guess = message.content.upper()
        if len(guess) != 5 or not guess.isalpha():
            await message.channel.send(embed=discord.Embed(
                title="Invalid Guess",
                description="Your guess must be a 5-letter word!\nType `/quit` to quit the game",
                color=discord.Color.orange()
            ), delete_after=5)
            return

        try:
            game = self.games[message.channel.id]
            game["last_interaction_time"] = time.time()
            
            original_message = await message.channel.fetch_message(game["message_id"])
            current_row = game["current_row"]

            if current_row >= 5:
                del self.games[message.channel.id]
                await message.channel.send(embed=discord.Embed(
                    title="Game Over",
                    description="The game is over! Start a new game with `/wordle`.",
                    color=discord.Color.red()
                ), delete_after=5)
                return

            target_word = game["target_word"]
            button_styles = [
                discord.ButtonStyle.success if guess[i] == target_word[i]
                else discord.ButtonStyle.danger if guess[i] in target_word
                else discord.ButtonStyle.secondary
                for i in range(5)
            ]

            view = discord.ui.View()
            for row in range(5):
                for col in range(5):
                    label = guess[col] if row == current_row else original_message.components[row].children[col].label
                    style = button_styles[col] if row == current_row else original_message.components[row].children[col].style
                    view.add_item(discord.ui.Button(label=label, style=style))

            embed = discord.Embed(
                title=f"Guess {current_row + 1}: **{guess}**",
                description="",
                color=discord.Color.yellow()
            )

            if game.get("hint"):
                embed.add_field(name="Hint", value=game["hint"], inline=False)

            await original_message.edit(embed=embed, view=view)
            await message.delete()
            
            if guess == target_word:
                del self.games[message.channel.id]
                await message.channel.send(embed=discord.Embed(
                    title="Congratulations!",
                    description=f"🎉 {message.author.mention} guessed the word **{target_word}** correctly!",
                    color=discord.Color.green()
                ))
            else:
                game["current_row"] += 1
                if game["current_row"] >= 5:
                    del self.games[message.channel.id]
                    await message.channel.send(embed=discord.Embed(
                        title="Game Over",
                        description=f"Game over! The word was **{target_word}**. Better luck next time!",
                        color=discord.Color.red()
                    ))

        except discord.NotFound:
            del self.games[message.channel.id]

async def setup(bot):
    await bot.add_cog(WordleGame(bot))