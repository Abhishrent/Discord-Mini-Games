# Discord Game Bot

A Discord bot featuring multiple classic games including Tic-Tac-Toe, Wordle, Memory Matching, and Sequence Memory games.

## Features

### Games Available
1. **Tic-Tac-Toe** (`/tictactoe` or `/ttt`)
   - Play against AI or another player
   - Smart AI using minimax algorithm
   - Interactive button-based interface
   - Configurable turn timer

2. **Wordle** (`/wordle`)
   - Classic word-guessing game
   - Custom word support with optional hints
   - Color-coded feedback
   - Adjustable game timeout
   - Support for 5-letter words

3. **Memory Matching** (`/memory`)
   - 5x5 grid of emoji pairs
   - Time-based scoring
   - Interactive button interface
   - Customizable inactivity timeout

4. **Sequence Memory** (`/sequence`)
   - Simon Says-style memory game
   - Progressive difficulty
   - Visual sequence display
   - Adjustable game timeout

## Commands

### Game Selection
- `/game [title]` - Main command to select and start games
  - Options: "Tic-Tac-Toe", "Wordle", "Memory Blocks", "Sequence Memoriser"

### Individual Game Commands
- `/tictactoe [player1] [player2]` - Start a Tic-Tac-Toe game
- `/wordle [word] [hint]` - Start a Wordle game (optional custom word and hint)
- `/memory` - Start a Memory Matching game
- `/sequence` - Start a Sequence Memory game
- `/quit` - Quit the current game (Wordle only)

### Admin Commands
- `/load [cog]` - Load a specific cog (owner only)
- `/unload [cog]` - Unload a specific cog (owner only)
- `/reload [cog]` - Reload a specific cog (owner only)
- `/switch [cog_to_unload] [cog_to_load]` - Switch between cogs (owner only)

## Installation

1. Clone the repository
2. Install required dependencies:
```bash
pip install -r requirements.txt
```
3. Set up your environment:
   - Create a `.env` file in the root directory
   - Add your bot token:
     ```
     BOT_TOKEN=your_discord_bot_token
     ```
   - Alternatively, you can directly set the token in `config.py`

4. Configure the bot in `config.py`:
```python
BOT_NAME = 'your_bot_name'
PREFIX = ('prefix_1 ', 'prefix_2 ')  # Configure your preferred command prefixes
```

5. Set up the word list:
   - Create/edit `words.txt` with your list of 5-letter words for the Wordle game

## File Structure
```
├── main.py            # Bot initialization and core functionality
├── config.py          # Configuration settings
├── requirements.txt   # Project dependencies
├── words.txt          # Wordle word list
├── cogs/
│   ├── game_selector.py   # Game selection interface
│   ├── tictactoe.py      # Tic-Tac-Toe game
│   ├── wordle.py         # Wordle game
│   ├── memory.py         # Memory Matching game
│   └── sequence.py       # Sequence Memory game
```

## Game Settings

Each game has configurable timeout settings that can be adjusted in their respective files:

- **Tic-Tac-Toe**: Turn timer settings in `tictactoe.py`
- **Wordle**: Game timeout settings in `wordle.py`
- **Memory Matching**: Inactivity timeout in `memory.py`
- **Sequence Memory**: Game timeout settings in `sequence.py`

Look for the `Game Settings` section at the top of each game file to modify these values.

## Technical Details

### Dependencies
- Python 3.8+
- discord.py 2.4.0
- python-dotenv (for environment variables)

### Key Features
- Button-based UI using Discord's interaction components
- Asynchronous game handling
- Automatic game cleanup
- Error handling and validation
- Configurable timeout management
- Dynamic cog loading system
- Slash command support
- Owner-only administrative commands

### Bot Configuration
The bot supports:
- Multiple command prefixes
- Environment variable configuration
- Dynamic cog loading/unloading
- Custom bot presence
- Slash command synchronization
- Error handling with interactive command listing
