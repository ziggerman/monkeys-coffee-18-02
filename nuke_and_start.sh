#!/bin/bash
echo "Attemping to kill all bot processes..."
pkill -9 -f "python.*bot.py"
pkill -9 -f "python.*bot"
pkill -9 -f "bot.py"
pkill -9 -f "main.py"
killall -9 python3
killall -9 Python
echo "Kill commands executed."
sleep 2
echo "Starting bot..."
python3 bot.py
