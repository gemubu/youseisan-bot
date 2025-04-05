import discord
from discord.ext import commands
from models import Birthdays
import re
import os

class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    # 誕生日登録コマンド
    @discord.app_commands.command(name='birthday', description='誕生日を登録します　mmdd形式で入力してください')
    async def birthday(self, ctx: discord.Interaction, user_str: str, birthday: str):
        """誕生日を登録する
        Args:
            user_str (str): ユーザー(メンション)
            birthday (str): 誕生日
        """
        if ctx.guild is None:
            await ctx.response.send_message(content='サーバー内で実行してください', ephemeral=True)
            return
        user_id = int(re.findall(r'\d+', user_str)[0])
        try:
            result = Birthdays.create(
                user_id=user_id, birthday=birthday, channel_id=ctx.channel.id)
            if result == 0:
                await ctx.response.send_message(content='登録しました')
            else:
                await ctx.response.send_message(content='すでに登録されています')
        except Exception as e:
            await ctx.response.send_message(content=f'error やり直して下さい', ephemeral=True)
            # await kushina.send(f'An error occurred: {e}')

    # 誕生日解除コマンド
    @discord.app_commands.command(name='del_birthday', description='誕生日を解除します 解除するユーザーをメンションしてください')
    async def del_birthday(self, ctx: discord.Interaction, user_str: str):
        """誕生日を解除する
        Args:
            user_str (str): ユーザー
        """
        if ctx.guild is None:
            await ctx.response.send_message(content='サーバー内で実行してください', ephemeral=True)
            return
        user_id = int(re.findall(r'\d+', user_str)[0])
        result = Birthdays.delete(
            user_id=user_id, channel_id=ctx.channel.id)
        if result == 0:
            await ctx.response.send_message(content='解除しました')
        else:
            await ctx.response.send_message(content='登録されていません')

    # 誕生日確認コマンド
    @discord.app_commands.command(name='check_birthday', description='登録されている誕生日を確認します')
    async def check_birthday(self, ctx: discord.Interaction):
        """誕生日を確認する
        """
        if ctx.guild is None:
            await ctx.response.send_message(content='サーバー内で実行してください')
            return
        birthday_list = Birthdays.filter(channel_id=ctx.channel.id)
        if len(birthday_list) == 0:
            await ctx.response.send_message(content='登録されていません')
            return
        sorted_birthday_list = sorted(birthday_list, key=lambda x: x['birthday'])
        embed = discord.Embed(title='登録されているユーザー', description='', color=0x00ff00)
        name_str = ''
        birth_str = ''
        for i in sorted_birthday_list:
            month = int(i['birthday'][0] + i['birthday'][1])
            day = int(i['birthday'][2] + i['birthday'][3])
            name_str += f'<@{i["user_id"]}>\n'
            birth_str += f'{month}月{day}日\n'
        embed.add_field(name='', value=name_str, inline=True)
        embed.add_field(name='', value=birth_str, inline=True)
        await ctx.response.send_message(embed=embed)

    async def birth_notification(self, date_str) -> None:
        """誕生日通知を送信する
        """
        birthday_list = Birthdays.all()
        for i in birthday_list:
            if i['birthday'] == date_str:
                await self.bot.get_channel(i[2]).send(f'今日は <@{i["user_id"]}> の誕生日です\nおめでとうございます')

async def setup(bot):
    await bot.add_cog(Birthday(bot))