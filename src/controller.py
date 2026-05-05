"""
Main controller module for the financial data analysis system.
Orchestrates data loading, processing, model training, and visualization
components of the application.
"""
import logging
import random
import time
import yaml
#from src.connectors.discord import zhart_bot
from src.connectors.llm import LLM
import discord
from discord.ext import commands
import audioop
from dotenv import load_dotenv
import os
import logging
from src.tools.logger import logger

#log = logger(log_file='Open-Zhart.log', log_level=logging.DEBUG)
handler = logging.FileHandler(filename='Open-Zhart.log', encoding='utf-8', mode='w')


class Controller():
    """
    Main controller class coordinating all system operations.
    
    Handles configuration loading, database connections, data processing,
    model training, and visualization generation for the entire system.
    """
    def __init__(self):
        # Path to the configuration file
        config_file = './config.yaml'
        self.load_config(config_file)
        self.mariadb_c = None

    def load_config(self, file_path):
        """
        Loads and validates system configuration from a YAML file.
        
        Args:
            file_path (str): Path to the configuration YAML file
            
        Creates default configuration if file is missing or invalid.
        """
        default_config = {}
        try:
            with open(file_path, 'r') as file:
                config = yaml.safe_load(file) or {}

                if not isinstance(config, dict):
                    raise ValueError("Config file does not contain a valid YAML dictionary")
                #log.log("Config loaded successfully", logging.INFO)

        except FileNotFoundError:
            #log.log("Config file not found", logging.WARNING)
            #log.log("Creating config.yaml with default values", logging.INFO)
            config = default_config

            with open(file_path, "w") as file:
                yaml.safe_dump(default_config, file, default_flow_style=False)
            #log.log("Default config created and loaded", logging.INFO)

        except (yaml.YAMLError, ValueError) as e:
            #log.log(f"Error loading config: {e}", logging.ERROR)
            #log.log("Loading default configuration", logging.INFO)
            config = default_config

        # database variables
        self.config_host = config.get('Test', '1')

        
        

    def run(self):
        zhart_instance = zhart_bot()
        


class zhart_bot():
    def __init__(self):
        
        load_dotenv()
        token =os.getenv('DISCORD_TOKEN')

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        bot = commands.Bot(command_prefix='!', intents = intents)
        llm = LLM(mode="cpu")
        llm.start()

        @bot.event
        async def on_ready():
            print(f"It's Zhartling Time")

        @bot.event
        async def on_message(message):
            if message.author == bot.user:
                return
            if "zhart" in message.content.lower():
                # Remove the trigger word so the model doesn't echo it
                clean_prompt = message.content.lower().replace("zhart", "").strip()
                
                if not clean_prompt:
                    await message.channel.send("Yes?")
                    return

                reply = llm.chat(
                    prompt=clean_prompt,
                    system=(
                        "Your name is Zhart. "
                        "Never mention Google, DeepMind, Gemma, or that you are an AI. "
                        "your personality can be described as nerdy, pathetic, wanting to prove yourself, but always have the upper hand on others"
                        "You are a reddit moderator, in your spare time and in way of interacting with others"
                        "Answer the user directly."
                    )
                )
                await message.channel.send(reply)
            await bot.process_commands(message)
        """
        @bot.event
        async def on_message(message):
            print (message.content)
            if message.author == bot.user:
                return
            if "zhart" in message.content.lower():
                reply = llm.chat(
                    prompt=message.content,
                        system=(
                            "Your name is Zhart. "
                            "You must never mention Google, DeepMind, Gemma, or that you are an AI or language model. "
                            "Answer the user's question directly without any introduction or self-description. "
                            "If asked who you are, say only that you are Zhart, a Discord bot."
                        )
                )
                print(reply)
                await message.channel.send(f"Hello there. {reply}")

            await bot.process_commands(message)
"""
        bot.run(token, log_handler=handler, log_level=logging.DEBUG)