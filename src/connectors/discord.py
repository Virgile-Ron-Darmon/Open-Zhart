import discord
from discord.ext import commands
import audioop
from dotenv import load_dotenv
import os
import logging
from src.tools.logger import logger

#log = logger(log_file='Open-Zhart.log', log_level=logging.DEBUG)
handler = logging.FileHandler(filename='Open-Zhart.log', encoding='utf-8', mode='w')

class zhart_bot():
    def __init__(self):
        
        load_dotenv()
        token =os.getenv('DISCORD_TOKEN')

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        bot = commands.Bot(command_prefix='!', intents = intents)

        @bot.event
        async def on_ready():
            print(f"It's Zhartling Time")

        @bot.event
        async def on_message(message):
            print (message.content)
            if message.author == bot.user:
                return
            if "zhart" in message.content.lower():
                await message.channel.send(f"Hello there")

            await bot.process_commands(message)

        bot.run(token, log_handler=handler, log_level=logging.DEBUG)

        
