import discord
from discord.ext import commands
import asyncio
from config import BOT_NAME

#---------Game Settings--------------#
TIMEOUT_DURATION = 60 #in seconds    #
#------------------------------------#

class TicTacToeGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @commands.hybrid_command(name="tictactoe", aliases=["ttt"], with_app_command=True)
    async def start_game(self, ctx: commands.Context, player1: discord.Member = None, player2: discord.Member = None):
        """
        Start a new Tic-Tac-Toe game.
        If no player2 is specified, the game defaults to AI as the opponent.
        """
        # Check if a game is already active in the channel
        if ctx.channel.id in self.games:
            await ctx.send(embed=discord.Embed(
                title="Game Already Active",
                description="A Tic-Tac-Toe game is already active in this channel! Please finish the current game before starting a new one.",
                color=discord.Color.red()
            ))
            return

        # Default player1 to the user who used the command
        player1 = player1 or ctx.author
        is_ai_game = player2 is None

        # Determine player2
        player2 = player2 if not is_ai_game else "AI"

        # Create initial game state
        view = discord.ui.View()

        # Create a 3x3 grid of buttons
        for row in range(3):
            for col in range(3):
                button = discord.ui.Button(
                    label="\u200b",
                    style=discord.ButtonStyle.secondary,
                    row=row,
                    custom_id=f"ttt_{row}_{col}",
                    disabled=True  # Initially disabled until game starts
                )
                button.callback = self.button_callback
                view.add_item(button)

        # Add Start/Quit Game button
        start_button = discord.ui.Button(
            label="Start Game",
            style=discord.ButtonStyle.primary,
            row=3,
            custom_id="start_game"
        )
        start_button.callback = self.start_button_callback
        view.add_item(start_button)

        # Create an embed message for starting the game
        embed = discord.Embed(
            title="Tic-Tac-Toe Game",
            description=f"**{player1.name}** vs **{player2.name if not is_ai_game else BOT_NAME}**\n\nClick 'Start Game' to begin!",
            color=discord.Color.green()
        )

        # Send the initial grid and embed
        message = await ctx.send(embed=embed, view=view)

        # Store game state
        self.games[ctx.channel.id] = {
            "board": [[None for _ in range(3)] for _ in range(3)],
            "players": {
                "X": player1,
                "O": player2
            },
            "current_player": "X",
            "message_id": message.id,
            "message": message,
            "is_ai_game": is_ai_game,
            "game_started": False,
            "owner": ctx.author.id
        }

        # Start the first turn timeout
        self.start_turn_timeout(ctx.channel.id)


    async def start_button_callback(self, interaction: discord.Interaction):
        """Handle Start/Quit Game button interaction"""
        if interaction.channel_id not in self.games:
            return

        game = self.games[interaction.channel_id]

        # If game is not started, start it
        if not game["game_started"]:
            game["game_started"] = True
            
            # Create new view with enabled buttons
            view = await self.create_game_view(game)
            
            embed = discord.Embed(
                title="Tic-Tac-Toe Game",
                description=f"{game['players']['X'].name}'s turn (X)",
                color=discord.Color.yellow()
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
        
        # If game is started, quit it
        else:
            embed = discord.Embed(
                title="Game Quit",
                description="The Tic-Tac-Toe game has been ended.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            del self.games[interaction.channel_id]

    async def create_game_view(self, game):
        """Create a new view with the current game state"""
        view = discord.ui.View()
        
        # Add game grid buttons
        for row in range(3):
            for col in range(3):
                button = discord.ui.Button(
                    label=game["board"][row][col] if game["board"][row][col] else "\u200b",
                    style=(
                        discord.ButtonStyle.success if game["board"][row][col] == "X" else
                        discord.ButtonStyle.danger if game["board"][row][col] == "O" else
                        discord.ButtonStyle.secondary
                    ),
                    row=row,
                    custom_id=f"ttt_{row}_{col}",
                    disabled=not game["game_started"] or game["board"][row][col] is not None
                )
                button.callback = self.button_callback
                view.add_item(button)

        # Add Start/Quit Game button
        start_button = discord.ui.Button(
            label="Quit Game" if game["game_started"] else "Start Game",
            style=discord.ButtonStyle.danger if game["game_started"] else discord.ButtonStyle.primary,
            row=3,
            custom_id="start_game"
        )
        start_button.callback = self.start_button_callback
        view.add_item(start_button)
        
        return view

    async def button_callback(self, interaction: discord.Interaction):
        """
        Handle button press in the Tic-Tac-Toe game.
        """
        # Ensure the game exists and has started
        if interaction.channel_id not in self.games:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Active Game",
                    description="There is no active Tic-Tac-Toe game in this channel.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        game = self.games[interaction.channel_id]
        
        if not game["game_started"]:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Game Not Started",
                    description="Please click 'Start Game' to begin playing!",
                    color=discord.Color.orange()
                ),
                ephemeral=True
            )
            return

        # Check if it's the correct player's turn
        if game["players"][game["current_player"]] != interaction.user and game["players"][game["current_player"]] != "AI":
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Your Turn",
                    description=f"It's {game['players'][game['current_player']].name}'s turn.",
                    color=discord.Color.orange()
                ),
                ephemeral=True
            )
            return

        # Parse button coordinates
        row, col = map(int, interaction.data['custom_id'].split('_')[1:])

        # Check if the cell is already occupied
        if game["board"][row][col] is not None:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Invalid Move",
                    description="This cell is already occupied!",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        # Acknowledge the interaction immediately
        await interaction.response.defer()

        # Cancel any existing timeout task
        if 'timeout_task' in game:
            game['timeout_task'].cancel()

        # Update game board
        game["board"][row][col] = game["current_player"]

        # Create updated view
        view = await self.create_game_view(game)

        # Check for win or draw
        result = self.check_game_status(game["board"])

        # Handle game progression
        if result is None:
            game["current_player"] = "O" if game["current_player"] == "X" else "X"
            
            # AI move if applicable
            if game["is_ai_game"] and game["current_player"] == "O":
                row, col = self.get_best_move(game["board"])
                game["board"][row][col] = "O"
                view = await self.create_game_view(game)
                result = self.check_game_status(game["board"])
                game["current_player"] = "X"

        # Update embed based on game state
        if result is not None:
            # Game ended
            if result == "X":
                embed = discord.Embed(
                    title="Game Over",
                    description=f"🎉 {game['players']['X'].name} wins!",
                    color=discord.Color.green()
                )
            elif result == "O":
                winner_name = game['players']['O'].name if not game["is_ai_game"] else BOT_NAME
                embed = discord.Embed(
                    title="Game Over",
                    description=f"🎉 {winner_name} wins!",
                    color=discord.Color.green()
                )
            else:  # Draw
                embed = discord.Embed(
                    title="Game Over",
                    description="It's a draw!",
                    color=discord.Color.blue()
                )
            del self.games[interaction.channel_id]
            await interaction.message.edit(embed=embed, view=None)
        else:
            # Game continues
            current_player_name = game['players'][game['current_player']].name
            embed = discord.Embed(
                title="Tic-Tac-Toe Game",
                description=f"{current_player_name}'s turn ({game['current_player']})",
                color=discord.Color.yellow()
            )
            await interaction.message.edit(embed=embed, view=view)

            # Start a timeout for the next player's turn
            self.start_turn_timeout(interaction.channel_id)


    def start_turn_timeout(self, channel_id):
        """
        Start a timeout task for the current player's turn.
        """
        timeout_duration = TIMEOUT_DURATION  # Timeout duration in seconds

        async def timeout_task():
            await asyncio.sleep(timeout_duration)
            # Handle timeout event
            if channel_id in self.games:
                game = self.games[channel_id]
                current_player = game["players"][game["current_player"]]
                if current_player != "AI":  # Skip timeout handling for AI
                    embed = discord.Embed(
                        title="Turn Timeout",
                        description=f"{current_player.name} took too long! Game over.",
                        color=discord.Color.red()
                    )
                    await game["message"].edit(embed=embed, view=None)
                    del self.games[channel_id]

        # Create and store the timeout task
        self.games[channel_id]['timeout_task'] = asyncio.create_task(timeout_task())


    def check_game_status(self, board):
        """
        Check if the game has a winner or is a draw.
        Returns 'X', 'O', 'Draw', or None
        """
        # Check rows
        for row in board:
            if row[0] == row[1] == row[2] and row[0] is not None:
                return row[0]

        # Check columns
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] and board[0][col] is not None:
                return board[0][col]

        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] and board[0][0] is not None:
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] and board[0][2] is not None:
            return board[0][2]

        # Check for draw
        if all(cell is not None for row in board for cell in row):
            return "Draw"

        # Game continues
        return None

    def get_best_move(self, board):
        """
        Use minimax algorithm to find the best move for the AI.
        """
        best_score = float('-inf')
        best_move = None

        for r in range(3):
            for c in range(3):
                if board[r][c] is None:
                    # Try this move
                    board[r][c] = "O"
                    # Calculate the move's score
                    score = self.minimax(board, 0, False)
                    # Undo the move
                    board[r][c] = None

                    # Update best move if score is better
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)

        return best_move

    def minimax(self, board, depth, is_maximizing):
        """
        Minimax algorithm with recursion to find the best move.
        """
        result = self.check_game_status(board)

        # Scoring
        if result == "O":
            return 10 - depth
        elif result == "X":
            return depth - 10
        elif result == "Draw":
            return 0

        if is_maximizing:
            best_score = float('-inf')
            for r in range(3):
                for c in range(3):
                    if board[r][c] is None:
                        board[r][c] = "O"
                        score = self.minimax(board, depth + 1, False)
                        board[r][c] = None
                        best_score = max(best_score, score)
            return best_score
        else:
            best_score = float('inf')
            for r in range(3):
                for c in range(3):
                    if board[r][c] is None:
                        board[r][c] = "X"
                        score = self.minimax(board, depth + 1, True)
                        board[r][c] = None
                        best_score = min(best_score, score)
            return best_score

async def setup(bot):
    await bot.add_cog(TicTacToeGame(bot))