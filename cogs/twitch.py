from twitchAPI.twitch import Twitch as Twitch_api
from twitchAPI.helper import first
import discord
from discord.ext import commands
import config
from models import Twitch as twitch_database
import datetime

class Twitch(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def create_twitch_embed(self, ctx: discord.Interaction, twitch: Twitch_api, twitch_name: str) -> discord.Embed:
        """twitchのユーザー情報を埋め込みに変換する
        Args:
            ctx (discord.Interaction): インタラクション
            twitch (Twitch): twitchAPIのインスタンス
            twitch_name (str): twitchのID
        Returns:
            discord.Embed: twitchのユーザー情報を埋め込みに変換したもの
        """
        user = await first(twitch.get_users(logins=[twitch_name]))
        if user is None:
            await ctx.response.send_message(content='ユーザーが見つかりません', ephemeral=True)
            return
        title = user.login
        if user.login == user.display_name:
            title = user.login
        else:
            title = f'{user.display_name} ({user.login})'
        user_follows = await twitch.get_channel_followers(broadcaster_id=user.id)
        embed = discord.Embed(title=title, description='',
                            url=f'https://www.twitch.tv/{user.login}', color=0x00ff00)
        embed.set_thumbnail(url=user.profile_image_url)
        embed.color = discord.Color.purple()
        embed.add_field(
            name='', value=f'{user_follows.total}人のフォロワー', inline=False)
        embed.add_field(name='', value=user.description, inline=False)
        return embed

    @discord.app_commands.command(name='twitch', description='twitchの通知を登録します')
    @discord.app_commands.describe(twitch_name='twitchのユーザーネーム')
    async def twitch(self, ctx: discord.Interaction, twitch_name: str):
        """twitchの通知を登録する
        このコマンドが送信されたチャンネルにtwitchの通知がされる
        Args:
            twitch_name (str): twitchのユーザーネーム
        """
        #try:
        twitch = await Twitch_api(config.TWITCH_ID, config.TWITCH_SECRET)
        embed = await self.create_twitch_embed(ctx, twitch, twitch_name)
        # *データベースに登録する
        result = twitch_database.create(twitch_username=twitch_name, channel_id=ctx.channel.id)
        if result == 0:
            await ctx.response.send_message(content='登録しました', embed=embed)
        else:
            await ctx.response.send_message(content='すでに登録されています', embed=embed)
        await twitch.close()


    @discord.app_commands.command(name='del_twitch', description='twitchの通知を解除します')
    @discord.app_commands.describe(twitch_name='twitchのユーザーネーム')
    async def del_twitch(self, ctx: discord.Interaction, twitch_name: str):
        """twitchの通知を解除する
        このコマンドが送信されたチャンネルにtwitchの通知がされなくなる
        Args:
            twitch_name (str): twitchのユーザーネーム
        """
        twitch = await Twitch_api(config.TWITCH_ID, config.TWITCH_SECRET)
        embed = await self.create_twitch_embed(ctx, twitch, twitch_name)
        result = twitch_database.delete(twitch_username=twitch_name, channel_id=ctx.channel.id)
        if result == 0:
            await ctx.response.send_message(content='解除しました', embed=embed)
        else:
            await ctx.response.send_message(content='登録されていません', embed=embed)
        await twitch.close()

    # twitch登録確認コマンド
    @discord.app_commands.command(name='check_twitch', description='twitchの通知を確認します')
    async def check_twitch(self, ctx: discord.Interaction):
        """twitchの通知を確認する
        このコマンドが送信されたチャンネルに登録されているtwitchのembedを表示する
        """
        twitch_list = twitch_database.filter(channel_id=ctx.channel.id)
        if len(twitch_list) == 0:
            await ctx.response.send_message(content='登録されていません')
            return
        twitch = await Twitch_api(config.TWITCH_ID, config.TWITCH_SECRET)
        await ctx.response.send_message(content='登録されているチャンネル')
        for i in twitch_list:
            embed = await self.create_twitch_embed(ctx, twitch, i["twitch_username"])
            await ctx.channel.send(embed=embed)
        await twitch.close()

    async def twitch_notification(self) -> None:
        """配信開始通知を送信する
        """
        async def check_history(time: str):
            messages = [message async for message in channel.history(limit=20)]
            for message in messages:
                try:
                    embed = message.embeds[0]
                    embed_dict = embed.to_dict()
                    embed_time = embed_dict['footer']['text']
                    if embed_time == time:
                        return message
                except:
                    pass
            return None

        twitch = await Twitch_api(config.TWITCH_ID, config.TWITCH_SECRET)
        twitch_user_list_of_dict= twitch_database.all()
        for user_dict in twitch_user_list_of_dict:
            stream = await first(twitch.get_streams(user_login=user_dict['twitch_username']))
            if stream is not None:
                streamer = await first(twitch.get_users(logins=user_dict['twitch_username']))
                stream_start_time = stream.started_at + datetime.timedelta(hours=9)
                stream_start_time_str = stream_start_time.strftime(
                    '%Y/%m/%d %H:%M:%S')
                channel = self.bot.get_channel(user_dict['channel_id'])
                message = await check_history(stream_start_time_str)
                if message is None:
                    embed = discord.Embed(
                        title=stream.title, url=f'https://www.twitch.tv/{streamer.login}', color=discord.Color.purple())
                    embed.set_author(name=streamer.display_name, icon_url=streamer.profile_image_url,
                                    url=f'https://www.twitch.tv/{streamer.login}')
                    stream_img = f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{user_dict['twitch_username']}-440x248.jpg"
                    embed.set_image(url=stream_img)
                    embed.add_field(
                        name='Game', value=stream.game_name, inline=False)
                    embed.set_footer(text=stream_start_time_str)
                    await self.bot.get_channel(user_dict['channel_id']).send(f'{streamer.display_name}が配信を開始しました', embed=embed)
        await twitch.close()


async def setup(bot):
    await bot.add_cog(Twitch(bot))