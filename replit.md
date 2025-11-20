# Discord Chess Bot

## Overview
A fully functional Discord bot that enables users to play chess games directly in Discord channels. The bot supports both player vs player (PvP) games and player vs AI games with multiple difficulty levels.

## Recent Changes
- December 20, 2024: Initial implementation completed
- Created Discord bot with slash commands
- Implemented chess game engine with move validation
- Added AI opponent with 4 difficulty levels (ultra_easy, easy, medium, destructive)
- Set up Discord bot workflow and verified connection
- Fixed AI evaluation algorithm for proper checkmate scoring
- Added robust user mention handling to prevent crashes
- Implemented end command restrictions for better security

## Features
- **PvP Chess Games**: Players can challenge each other to chess matches
- **AI Opponent**: Built-in AI with 4 difficulty levels (ultra_easy, easy, medium, destructive)
- **Slash Commands**: Modern Discord slash commands for all interactions
- **Move Validation**: Full chess rule validation using python-chess library
- **Visual Board Display**: Unicode chess board representation in Discord embeds
- **Game Management**: Start, move, show board, forfeit, and help commands

## Commands
- `/chess @opponent` - Start a PvP game against another user
- `/chess difficulty:easy` - Start an AI game with specified difficulty
- `/move e2e4` - Make a move using UCI notation
- `/show` - Display the current board state
- `/end` - End the current game
- `/help` - Show help information

## Technical Architecture
- **Language**: Python 3.11
- **Discord Library**: discord.py
- **Chess Engine**: python-chess for move validation and board representation
- **AI Implementation**: Custom minimax algorithm with alpha-beta pruning
- **Bot Type**: Discord slash command bot with proper intents

## Dependencies
- discord.py: Discord bot framework
- python-chess: Chess game logic and validation
- chess: Additional chess utilities

## Environment Variables
- `DISCORD_BOT_TOKEN`: Discord bot authentication token (managed as Replit secret)

## Current State
- ✅ Bot successfully connected to Discord
- ✅ All 5 slash commands synced
- ✅ Chess engine operational
- ✅ AI opponent functional
- ✅ PvP games supported
- ✅ Workflow running in background

The bot is now ready for use in Discord servers!