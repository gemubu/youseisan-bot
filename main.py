import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# discord.opus.load_opus('/opt/homebrew/lib/libopus.dylib')  # M1/M2 Macの場合

#! テストする時は関係ないcogはコメントアウトする
#! 今コメントアウトしてるやつはコード変更で動かなくなってる。ごめん
INITIAL_EXTENSIONS = [
    'cogs.general',
    'cogs.admin',
    #'cogs.twitch',
    #'cogs.birthday',
    #'cogs.event',
    #'cogs.level',
    'cogs.tts',
]

intents = discord.Intents.all()
intents.typing = False

class MyBot(commands.Bot):
    async def setup_hook(self):
        for cog in INITIAL_EXTENSIONS:
            await self.load_extension(cog)
        await self.tree.sync()

bot = MyBot(command_prefix='!', intents=intents)

bot.run(BOT_TOKEN)