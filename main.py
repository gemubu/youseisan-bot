import discord
from discord.ext import commands
import config


INITIAL_EXTENSIONS = [
    'cogs.general',
    'cogs.admin',
    'cogs.twitch',
    'cogs.birthday',
    'cogs.event',
    'cogs.level',
]

intents = discord.Intents.all()
intents.typing = False

class MyBot(commands.Bot):
    async def setup_hook(self):
        for cog in INITIAL_EXTENSIONS:
            await self.load_extension(cog)
        await self.tree.sync()

bot = MyBot(command_prefix='!', intents=intents)

bot.run(config.TEST_TOKEN)