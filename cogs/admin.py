import discord
from discord.ext import commands, tasks
import datetime
from cogs import twitch
from cogs import birthday
from models import Guilds


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.twitch = twitch.Twitch(self.bot)
        self.birthday = birthday.Birthday(self.bot)

    @commands.Cog.listener()
    async def on_ready(self):
        self.loop.start()
        channel = self.bot.get_channel(1222457963986419722)
        DIFF_JST_FROM_UTC = 9
        jp_time = datetime.datetime.now(datetime.timezone.utc) + \
            datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        day = jp_time.strftime('%m/%d')
        time = jp_time.strftime('%H:%M')
        await channel.send(f'起動したよ{day} {time}')

        for guild in self.bot.guilds:
            a = Guilds.create_or_update(discord_id=guild.id, name=guild.name, icon=f"{guild.icon}", owner_id=guild.owner_id)


    @tasks.loop(seconds=60)
    async def loop(self) -> None:
        try:
            await self.twitch.twitch_notification() # 配信開始通知
            # *日本時間に変換
            DIFF_JST_FROM_UTC = 9
            jp_time = datetime.datetime.now(
                datetime.timezone.utc) + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
            date_str = jp_time.strftime('%m%d')
            time_str = jp_time.strftime('%H:%M')
            dow = jp_time.weekday()
            # channel = client.get_channel(1222457963986419722) #!管理用のチャンネル　普段は消す
            # *00:00にメッセージを送信
            if time_str == '00:00':
                await self.birthday.birth_notification(date_str)
                # *シフトの提出の日
                if dow == 3:
                    user = self.bot.get_user(785868066525020170)
                    await user.send('シフトの提出の日だお')
            # *22:00にメッセージを送信
            if time_str == '22:00' and dow == 3:
                user = self.bot.get_user(785868066525020170)
                await user.send('早くシフトだせ')
        except Exception as e:
            user = self.bot.get_user(785868066525020170)
            await user.send(f'An error occurred: {e}')

async def setup(bot):
    await bot.add_cog(Admin(bot))