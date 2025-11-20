from keep_alive import keep_alive
import os
import discord
from discord.ext import commands
import chess
import chess.svg
import asyncio
import random
import io
from PIL import Image, ImageDraw, ImageFont
import tempfile
import json

# Bot setup with proper intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Dictionary to store active games
# Key: channel ID
# Value: dictionary with 'board', 'players', 'type', 'difficulty'
active_games = {}

# AI difficulty levels with move selection logic (1-20 scale)
def get_difficulty_settings(level):
    """Get AI settings for difficulty level 1-20"""
    if level < 1 or level > 20:
        level = 10  # Default to medium
    
    # Scale depth from 1-5 based on difficulty
    depth = min(1 + (level - 1) // 4, 5)
    
    # Scale randomness from 0.8 (level 1) to 0.0 (level 20)
    randomness = max(0.0, 0.8 - (level - 1) * 0.04)
    
    return {'depth': depth, 'randomness': randomness}

def save_games():
    """Save all active games to JSON file"""
    try:
        games_data = {}
        for channel_id, game_state in active_games.items():
            # Convert board to FEN string for saving
            games_data[str(channel_id)] = {
                'board_fen': game_state['board'].fen(),
                'players': game_state['players'],
                'type': game_state['type'],
                'difficulty': game_state.get('difficulty')
            }
        
        with open('saved_games.json', 'w') as f:
            json.dump(games_data, f, indent=2)
    except Exception as e:
        print(f"Error saving games: {e}")

def load_games():
    """Load active games from JSON file"""
    global active_games
    try:
        if os.path.exists('saved_games.json'):
            with open('saved_games.json', 'r') as f:
                games_data = json.load(f)
            
            for channel_id_str, game_data in games_data.items():
                channel_id = int(channel_id_str)
                
                # Reconstruct board from FEN
                board = chess.Board(game_data['board_fen'])
                
                # Reconstruct game state
                game_state = {
                    'board': board,
                    'players': tuple(game_data['players']),
                    'type': game_data['type']
                }
                
                # Add AI and difficulty for AI games
                if game_data['type'] == 'ai' and game_data.get('difficulty'):
                    game_state['difficulty'] = game_data['difficulty']
                    game_state['ai'] = SimpleAI(game_data['difficulty'])
                
                active_games[channel_id] = game_state
            
            print(f"Loaded {len(active_games)} saved games")
    except Exception as e:
        print(f"Error loading games: {e}")
        active_games = {}

def generate_chess_board_image(board, difficulty=None):
    """Generate a PNG image of the chess board using PIL"""
    # Board dimensions
    square_size = 50
    label_size = 20
    title_height = 30 if difficulty else 0
    board_size = square_size * 8
    total_width = board_size + label_size * 2
    total_height = board_size + label_size * 2 + title_height
    
    # Create image with space for labels and title
    img = Image.new('RGB', (total_width, total_height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw title with difficulty if AI game
    if difficulty:
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            title_font = ImageFont.load_default()
        
        title_text = f"AI Difficulty: {difficulty}"
        draw.text((total_width // 2, title_height // 2), title_text, fill='black', 
                 font=title_font, anchor='mm')
    
    # Colors
    light_square = '#F0D9B5'
    dark_square = '#B58863'
    
    # Board offset for labels and title
    board_x_offset = label_size
    board_y_offset = label_size + title_height
    
    # Draw board squares
    for rank in range(8):
        for file in range(8):
            x1 = board_x_offset + file * square_size
            y1 = board_y_offset + rank * square_size
            x2 = x1 + square_size
            y2 = y1 + square_size
            
            # Determine square color
            is_light = (rank + file) % 2 == 0
            color = light_square if is_light else dark_square
            
            draw.rectangle([x1, y1, x2, y2], fill=color)
    
    # Draw rank and file labels
    try:
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        label_font = ImageFont.load_default()
    
    # Files (a-h) at bottom and top
    for file in range(8):
        file_letter = chr(ord('a') + file)
        x = board_x_offset + file * square_size + square_size // 2
        
        # Bottom labels
        draw.text((x, board_y_offset + board_size + label_size // 2), file_letter, 
                 fill='black', font=label_font, anchor='mm')
        # Top labels
        draw.text((x, board_y_offset - label_size // 2), file_letter, 
                 fill='black', font=label_font, anchor='mm')
    
    # Ranks (1-8) at left and right
    for rank in range(8):
        rank_number = str(8 - rank)  # Flip for display (8 at top, 1 at bottom)
        y = board_y_offset + rank * square_size + square_size // 2
        
        # Left labels
        draw.text((label_size // 2, y), rank_number, 
                 fill='black', font=label_font, anchor='mm')
        # Right labels
        draw.text((board_x_offset + board_size + label_size // 2, y), rank_number, 
                 fill='black', font=label_font, anchor='mm')
    
    # Unicode chess pieces (for drawing text)
    piece_symbols = {
        'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',  # White
        'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'   # Black
    }
    
    # Draw pieces
    try:
        # Try to use a larger font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    for rank in range(8):
        for file in range(8):
            square = chess.square(file, 7-rank)  # Flip rank for display
            piece = board.piece_at(square)
            
            if piece:
                piece_char = piece_symbols.get(piece.symbol(), piece.symbol())
                
                # Calculate text position (centered in square, accounting for offsets)
                x = board_x_offset + file * square_size + square_size // 2
                y = board_y_offset + rank * square_size + square_size // 2
                
                # Draw piece
                draw.text((x, y), piece_char, fill='black', font=font, anchor='mm')
    
    # Convert to BytesIO for Discord
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer

class SimpleAI:
    """Simple chess AI that evaluates positions and makes moves"""
    
    def __init__(self, difficulty=10):
        self.difficulty = get_difficulty_settings(difficulty)
    
    def evaluate_board(self, board):
        """Simple board evaluation function"""
        if board.is_checkmate():
            # If it's checkmate, the side to move has lost
            # Return positive score for Black advantage, negative for White advantage
            return 9999 if board.turn == chess.WHITE else -9999
        if board.is_stalemate():
            return 0
        
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
        }
        
        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values[piece.piece_type]
                score += value if piece.color == chess.BLACK else -value
        
        return score
    
    def minimax(self, board, depth, alpha, beta, maximizing):
        """Minimax algorithm with alpha-beta pruning"""
        if depth == 0 or board.is_game_over():
            return self.evaluate_board(board)
        
        if maximizing:
            max_eval = -float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def get_best_move(self, board):
        """Get the best move for the AI"""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        # Add randomness based on difficulty
        if random.random() < self.difficulty['randomness']:
            return random.choice(legal_moves)
        
        best_move = None
        best_value = -float('inf')
        
        for move in legal_moves:
            board.push(move)
            move_value = self.minimax(board, self.difficulty['depth'], -float('inf'), float('inf'), False)
            board.pop()
            
            if move_value > best_value:
                best_value = move_value
                best_move = move
        
        return best_move if best_move else random.choice(legal_moves)

@bot.event
async def on_ready():
    """Bot startup event"""
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    
    # Load saved games
    load_games()
    
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@bot.tree.command(name="chess", description="Start a new chess game against AI or another player")
async def start_chess_game(
    interaction: discord.Interaction,
    opponent: discord.Member = None,
    difficulty: int = None
):
    """Start a new chess game"""
    channel_id = interaction.channel.id
    player1 = interaction.user
    
    if channel_id in active_games:
        await interaction.response.send_message(
            "A game is already in progress in this channel. Use `/move` to play or `/end` to stop the current game.",
            ephemeral=True
        )
        return
    
    board = chess.Board()
    
    if opponent:
        # PvP Game
        if player1.id == opponent.id:
            await interaction.response.send_message("You can't play against yourself!", ephemeral=True)
            return
        
        active_games[channel_id] = {
            'board': board,
            'players': (player1.id, opponent.id),  # White, Black
            'type': 'pvp'
        }
        save_games()  # Save after creating new game
        
        embed = discord.Embed(
            title="♟️ Chess Game Started!",
            description=f"**{player1.mention}** (White) vs **{opponent.mention}** (Black)\n\nIt's **{player1.mention}'s** turn!",
            color=0x8B4513
        )
        embed.add_field(name="Board", value=f"```\n{board.unicode()}\n```", inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    else:
        # AI Game
        if not difficulty or difficulty < 1 or difficulty > 20:
            await interaction.response.send_message(
                "Please select a difficulty level from 1 to 20 (1 = easiest, 20 = hardest)",
                ephemeral=True
            )
            return
        
        active_games[channel_id] = {
            'board': board,
            'players': (player1.id, None),  # White (player), Black (AI)
            'type': 'ai',
            'difficulty': difficulty,
            'ai': SimpleAI(difficulty)
        }
        save_games()  # Save after creating new game
        
        embed = discord.Embed(
            title="♟️ Chess vs AI Started!",
            description=f"**{player1.mention}** vs AI (Difficulty: **{difficulty}**)\n\nYou are White - make your move!",
            color=0x8B4513
        )
        embed.add_field(name="Board", value=f"```\n{board.unicode()}\n```", inline=False)
        embed.add_field(name="How to move", value="Use `/move e2e4` format", inline=False)
        
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="move", description="Make a move in the current chess game")
async def make_move(interaction: discord.Interaction, move: str):
    """Make a move in the chess game"""
    channel_id = interaction.channel.id
    
    if channel_id not in active_games:
        await interaction.response.send_message(
            "No game is currently in progress. Use `/chess` to start one.",
            ephemeral=True
        )
        return
    
    game_state = active_games[channel_id]
    board = game_state['board']
    game_type = game_state['type']
    
    # Parse the move - support both UCI (e2e4) and SAN (e4, Nf3, O-O) notation
    try:
        # First try SAN notation (e4, Nf3, O-O, etc.)
        user_move = board.parse_san(move)
    except ValueError:
        try:
            # If SAN fails, try UCI notation (e2e4, g1f3, etc.)
            user_move = board.parse_uci(move)
        except ValueError:
            await interaction.response.send_message(
                f"Invalid move format: `{move}`. Please use standard notation like `e4`, `Nf3`, `O-O` or UCI format like `e2e4`.",
                ephemeral=True
            )
            return
    
    if user_move not in board.legal_moves:
        await interaction.response.send_message(
            f"Invalid move: `{move}`. That is not a legal move.",
            ephemeral=True
        )
        return
    
    if game_type == 'pvp':
        # PvP logic
        players = game_state['players']
        current_turn_player_id = players[0] if board.turn == chess.WHITE else players[1]
        
        if interaction.user.id != current_turn_player_id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        
        board.push(user_move)
        save_games()  # Save after move
        
        if board.is_game_over():
            await handle_game_over(interaction, board, move, board.result(), players, game_type)
            return
        
        next_player_id = players[0] if board.turn == chess.WHITE else players[1]
        next_player = bot.get_user(next_player_id) or (interaction.guild.get_member(next_player_id) if interaction.guild else None)
        next_player_mention = next_player.mention if next_player else f"<@{next_player_id}>"
        
        embed = discord.Embed(
            title="♟️ Move Made",
            description=f"**{interaction.user.mention}** played: `{move}`\n\nIt's **{next_player_mention}'s** turn!",
            color=0x8B4513
        )
        embed.add_field(name="Board", value=f"```\n{board.unicode()}\n```", inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    elif game_type == 'ai':
        # AI game logic
        player_id = game_state['players'][0]
        if interaction.user.id != player_id:
            await interaction.response.send_message("You are not in the current game.", ephemeral=True)
            return
        
        board.push(user_move)
        save_games()  # Save after move
        
        if board.is_game_over():
            await handle_game_over(interaction, board, move, board.result(), game_state['players'], game_type)
            return
        
        # AI's turn
        ai = game_state['ai']
        ai_move = ai.get_best_move(board)
        
        if ai_move:
            board.push(ai_move)
            save_games()  # Save after AI move
        
        if board.is_game_over():
            await handle_game_over(interaction, board, move, board.result(), game_state['players'], game_type, ai_move)
        else:
            embed = discord.Embed(
                title="♟️ Moves Made",
                description=f"You played: `{move}`\nAI played: `{ai_move}`\n\nYour turn!",
                color=0x8B4513
            )
            embed.add_field(name="Board", value=f"```\n{board.unicode()}\n```", inline=False)
            
            await interaction.response.send_message(embed=embed)

async def handle_game_over(interaction, board, last_move, result, players, game_type, ai_move=None):
    """Handle the end of a game"""
    channel_id = interaction.channel.id
    
    embed = discord.Embed(title="🎉 Game Over!", color=0x00FF00)
    
    if game_type == 'pvp':
        winner_id = None
        if result == '1-0':
            winner_id = players[0]
        elif result == '0-1':
            winner_id = players[1]
        
        if winner_id:
            winner = bot.get_user(winner_id) or (interaction.guild.get_member(winner_id) if interaction.guild else None)
            winner_mention = winner.mention if winner else f"<@{winner_id}>"
            winner_text = f"**{winner_mention}** wins!"
        else:
            winner_text = "It's a draw!"
        
        embed.description = f"**{interaction.user.mention}** played: `{last_move}`\n{winner_text}"
        
    elif game_type == 'ai':
        move_text = f"You played: `{last_move}`"
        if ai_move:
            move_text += f"\nAI played: `{ai_move}`"
        
        if result == '1-0':
            result_text = "You won! 🎉"
        elif result == '0-1':
            result_text = "AI won! 🤖"
        else:
            result_text = "It's a draw! 🤝"
        
        embed.description = f"{move_text}\n\n{result_text}"
    
    embed.add_field(name="Final Board", value=f"```\n{board.unicode()}\n```", inline=False)
    embed.add_field(name="Result", value=f"`{result}`", inline=False)
    
    await interaction.response.send_message(embed=embed)
    del active_games[channel_id]
    save_games()  # Save after game ends

@bot.tree.command(name="end", description="End the current chess game")
async def end_game(interaction: discord.Interaction):
    """End the current chess game"""
    channel_id = interaction.channel.id
    
    if channel_id not in active_games:
        await interaction.response.send_message("No game is currently in progress to end.", ephemeral=True)
        return
    
    game_state = active_games[channel_id]
    user_id = interaction.user.id
    
    # Check if user is a participant in the game or has manage messages permission  
    has_manage_permission = False
    if interaction.guild:
        member = interaction.guild.get_member(user_id)
        has_manage_permission = member and member.guild_permissions.manage_messages
    
    if user_id not in game_state['players'] and not has_manage_permission:
        await interaction.response.send_message("You can only end games you're participating in!", ephemeral=True)
        return
    
    del active_games[channel_id]
    save_games()  # Save after manually ending game
    await interaction.response.send_message("The current chess game has been ended.", ephemeral=True)

@bot.tree.command(name="show", description="Show the current chess board")
async def show_board(interaction: discord.Interaction):
    """Show the current board state"""
    channel_id = interaction.channel.id
    
    if channel_id in active_games:
        game_state = active_games[channel_id]
        board = game_state['board']
        
        if game_state['type'] == 'pvp':
            players = game_state['players']
            white_player = bot.get_user(players[0]) or (interaction.guild.get_member(players[0]) if interaction.guild else None)
            black_player = bot.get_user(players[1]) or (interaction.guild.get_member(players[1]) if interaction.guild else None)
            current_player = white_player if board.turn == chess.WHITE else black_player
            white_mention = white_player.mention if white_player else f"<@{players[0]}>"
            black_mention = black_player.mention if black_player else f"<@{players[1]}>"
            current_mention = current_player.mention if current_player else (white_mention if board.turn == chess.WHITE else black_mention)
            description = f"**White:** {white_mention}\n**Black:** {black_mention}\n\n**{current_mention}'s** turn"
        else:
            description = f"You vs AI (Difficulty: {game_state['difficulty']})\n\n{'Your' if board.turn == chess.WHITE else 'AI'} turn"
        
        # Generate board image (pass difficulty for AI games)
        difficulty = game_state.get('difficulty') if game_state['type'] == 'ai' else None
        board_image = generate_chess_board_image(board, difficulty)
        
        embed = discord.Embed(
            title="♟️ Current Board",
            description=description,
            color=0x8B4513
        )
        
        # Attach the board image
        file = discord.File(board_image, filename="chess_board.png")
        embed.set_image(url="attachment://chess_board.png")
        
        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)
    else:
        await interaction.response.send_message("No game is currently in progress.", ephemeral=True)

@bot.tree.command(name="help", description="Show chess bot help")
async def chess_help(interaction: discord.Interaction):
    """Show help information"""
    embed = discord.Embed(
        title="♟️ Chess Bot Help",
        description="Play chess games directly in Discord!",
        color=0x8B4513
    )
    
    embed.add_field(
        name="Commands",
        value="""
        `/chess @opponent` - Start PvP game
        `/chess difficulty:10` - Start AI game
        `/move e2e4` - Make a move
        `/show` - Show current board as image
        `/end` - End current game
        `/help` - Show this help
        """,
        inline=False
    )
    
    embed.add_field(
        name="AI Difficulty Levels",
        value="""
        Choose from **1 to 20**:
        • 1-5: Very Easy (lots of mistakes)
        • 6-10: Easy (some mistakes)
        • 11-15: Medium (decent play)
        • 16-20: Hard (strong play)
        """,
        inline=False
    )
    
    embed.add_field(
        name="Move Formats",
        value="""
        **Standard Notation (SAN):** `e4`, `Nf3`, `Qxh5`, `O-O`, `O-O-O`
        **UCI Notation:** `e2e4`, `g1f3`, `d1h5`, `e1g1`, `e1c1`
        Both formats work! Use whichever you prefer.
        """,
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
if not token:
    print("❌ DISCORD_BOT_TOKEN environment variable not set!")
    print("Please set your Discord bot token as a secret.")
    exit(1)

# 1. ADD THE KEEP-ALIVE CALL HERE:
keep_alive()

print("🤖 Starting Chess Bot...")
bot.run(token)
