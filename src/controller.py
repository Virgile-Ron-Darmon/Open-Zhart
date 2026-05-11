"""
Main controller module for the financial data analysis system.
Orchestrates data loading, processing, model training, and visualization
components of the application.
"""
import logging
import yaml
from src.personality.personality import BotPersonality
import discord
from discord.ext import commands
import audioop
from dotenv import load_dotenv
import os
import logging


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
            config = default_config

        # database variables
        self.config_host = config.get('Test', '1')
        self.mode = config.get('Mode', 'cpu')
        self.model_path = config.get('Model_path', 'cpu')


    def run(self):

        self.Zhart_personality = BotPersonality(self.mode, self.model_path)

        load_dotenv()
        token =os.getenv('DISCORD_TOKEN')

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        bot = commands.Bot(command_prefix='!', intents = intents)


        @bot.event
        async def on_ready():
            print("It's Zhartling Time")

        @bot.event
        async def on_message(message):
            mode = 0
            if message.author == bot.user:
                return
            if bot.user in message.mentions:
                mode = 2
            elif bot.user in message.content.lower():
                mode = 1
                # Remove the trigger word so the model doesn't echo it
            
            reply = self.Zhart_personality.message_processor(message=message, mode=mode)
            print("0=============================")
            print(reply)
            print("=============================0")
            if reply != "":
                await message.channel.send(reply)
            await bot.process_commands(message)

        bot.run(token, log_handler=handler, log_level=logging.DEBUG)
