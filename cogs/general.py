import discord
from discord.ext import commands
import re
import random
import asyncio
import datetime
from models import ServerLevels


class General(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @discord.app_commands.command(name='team', description='チーム分けを行う')
    @discord.app_commands.describe(num_team='チーム数', exclude_member='除外するメンバー', auto='チーム分け後に自動でVCを移動するかどうか(何かしら入力されてたら今いるVCのすぐ下にチームVCが作成され、自動で送られます)')
    async def team(self, ctx: discord.Interaction, num_team: int = 2,
                exclude_member: str = None,
                auto: str = None):
        """チーム分けを行う
        Args:
            num_team (int): チーム数
            exclude_member (str): 除外するメンバー
            auto (str): チーム分け後に自動でVCを移動するかどうか(何かしら入力されてたら今いるVCのすぐ下にチームVCが作成され、自動で送られます)
        """
        # ボイスチャンネルに参加しているメンバーを取得
        try:
            members = [i.id for i in ctx.user.voice.channel.members]
        except AttributeError:
            await ctx.response('ボイスチャンネルに参加してからコマンドを実行してください')
            return
        # 除外するメンバーを取得
        if exclude_member:
            p = r'@(.*?>)'
            exclude_ids = re.findall(p, exclude_member)
            for i in range(len(exclude_ids)):
                try:
                    members.remove(int(exclude_ids[i]))
                except:
                    pass
        # チーム分け
        team_list = divide_list(members, num_team)
        # チーム分け結果を文字列に変換
        embed = discord.Embed(title='チーム分け結果', color=0x00ff00)
        for i in range(num_team):
            team = ''
            for j in range(len(team_list[i])):
                team += f'<@{team_list[i][j]}>\n'
            embed.add_field(name=f'Team{i+1}', value=team, inline=False)
        # メッセージを送信
        await ctx.response.send_message(embed=embed)
        # 自動でVCを移動
        if auto:
            category = ctx.user.voice.channel.category
            for i in range(num_team):
                voice_channel = await category.create_voice_channel(name=f'##Team{i+1}##')
                for j in range(len(team_list[i])):
                    member = ctx.guild.get_member(team_list[i][j])
                    await member.move_to(voice_channel)
            await ctx.channel.send('チーム分けが完了しました')

    @discord.app_commands.command(name='dice', description='ダイスを振ります')
    @discord.app_commands.describe(num='ダイスの個数')
    async def dice(self, ctx: discord.Interaction, num: int = 1):
        """ダイスを振る
        Args:
            num (int): ダイスの個数
        """
        dice_result = [random.randint(1, 6) for _ in range(num)]
        total = sum(dice_result)
        result_str = ''
        for i in range(num):
            result_str += f'dice{i+1} : {dice_result[i]}\n'
        result_str += f'-----------\n合計 : {total}'
        embed = discord.Embed(
            title='ダイス結果', description=result_str, color=0xffffff)
        await ctx.response.send_message(embed=embed)

    @discord.app_commands.command(name='r', description='募集を行います')
    async def r(self, ctx: discord.Interaction, title: str, detail: str = None, max: int = None, role: str = None, channel: str = None):
        """募集を行う
        Args:
            title (str): 募集タイトル
            detail (str): 募集内容
            max (int): 募集人数
            role (str): 付与するロール
            channel (str): 新たなチャンネルを作成するかどうか
        """
        embed = discord.Embed(title=title, description=detail, color=0x00ff00)
        name = '参加者'
        name += f' (1/{max})' if max else ' (1)'
        embed.add_field(name=name, value=f'<@{ctx.user.id}>', inline=False)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label='参加', style=discord.ButtonStyle.primary, custom_id="join"))
        view.add_item(discord.ui.Button(
            label='辞退', style=discord.ButtonStyle.primary, custom_id="cancel"))
        view.add_item(discord.ui.Button(
            label='終了', style=discord.ButtonStyle.red, custom_id="delete"))
        view.add_item(discord.ui.Button(
            label='再送', style=discord.ButtonStyle.green, custom_id="resend"))
        if role:
            role_ = await ctx.guild.create_role(name=role)
            await ctx.user.add_roles(role_)
            embed.add_field(name='', value=f'付与するロール:{role_.mention}', inline=False)

        if channel:
            c: discord.TextChannel = await ctx.channel.category.create_text_channel(name=f'__{title}__')
            await ctx.response.send_message(content=f'募集を行います {c.mention}')
            await c.send(embed=embed, view=view)
        else:
            await ctx.response.send_message(embed=embed, view=view)

    @discord.app_commands.command(name='vc', description='VC名を変更します VC名に"##"が含まれているVCのみ名前を変更できます')
    async def vc(self, ctx: discord.Interaction, name: str):
        """VC名を変更する
        Args:
            name (str): 変更後のVC名
        """
        try:
            # *VC名に'##'が含まれていないときVCの名前を変更できない
            if '##' not in ctx.user.voice.channel.name:
                await ctx.response.send_message(content=f'<@{ctx.user.id}> VC名に"##"が含まれているVCのみ名前を変更できます', ephemeral=True)
                return
            else:
                await ctx.user.voice.channel.edit(name=f'##{name}##')
                await ctx.response.send_message(content=f'VC名を{name}に変更しました', ephemeral=True)
        except AttributeError:
            await ctx.response.send_message(content=f'<@{ctx.user.id}> ボイスチャンネルに参加してからコマンドを実行してください', ephemeral=True)

    #抽選コマンド
    @discord.app_commands.command(name='select', description='指定された人数抽選します')
    async def select(self, ctx: discord.Interaction, num: int):
        embed = discord.Embed(title='セレクトからユーザーを選択', description=num, color=0x00ff00)
        embed.add_field(name='ユーザー', value='')
        select = discord.ui.UserSelect(max_values=25)
        view = discord.ui.View()
        view.add_item(select)
        view.add_item(discord.ui.Button(
            label='select', style=discord.ButtonStyle.primary, custom_id="select"))
        await ctx.response.send_message(embed=embed, view=view)

    # embed作成コマンド
    @discord.app_commands.command(name='embed', description='埋め込みメッセージを作成します')
    async def embed(self, ctx: discord.Interaction):
        try:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.user: discord.PermissionOverwrite(read_messages=True)
            }
            if ctx.channel.category is None:
                channel = await ctx.guild.create_text_channel(f'{ctx.user.name}-embed', overwrites=overwrites)
            else:
                channel = await ctx.channel.category.create_text_channel(f'{ctx.user.name}-embed', overwrites=overwrites)
            await ctx.response.send_message(content=f'埋め込みメッセージを作成します {channel.jump_url}', ephemeral=True)
            example_embed = discord.Embed(
                title='title', description='desc', color=0x00ff00)
            example_embed.add_field(
                name='fieldの名前部分', value='fieldの文章部分', inline=False)
            example_embed.set_footer(
                text=f'{ctx.user.name}', icon_url=ctx.user.avatar.url)
            example_embed.set_thumbnail(
                url=self.bot.get_user(814465495914119218).avatar.url)
            await channel.send(content='Example', embed=example_embed)
            help_embed = discord.Embed(
                title='--埋め込みメッセージ作成ヘルプ--', description='埋め込みメッセージを作成します\n埋め込みメッセージを送信するにはsendを入力してください\n埋め込みメッセージの作成を終了するにはendを入力してください', color=0x00ff00)
            help_embed.add_field(
                name='--コマンド一覧--', value='タイトルの追加 -> title\n説明の追加 -> desc\nフィールドの追加 -> field\n写真を追加 -> pic\nタイムスタンプを付与 -> time\n色を変更 -> color\n埋め込みを送信 -> send\n送信せずに終了 -> end', inline=False)
            help_message = await channel.send(embed=help_embed)
            empty_embed = discord.Embed(
                title='埋め込みは空です', description='', color=0x000000)
            embed = discord.Embed(title='', description='', color=0x000000)
            embed.set_footer(text=f'{ctx.user.name}', icon_url=ctx.user.avatar.url)
            preview_message = await channel.send('プレビュー', embed=empty_embed)

            def check(m: discord.Message):
                return m.channel == channel and m.author == ctx.user
            while True:
                try:
                    message = await self.bot.wait_for('message', check=check, timeout=300)
                    await message.delete()
                    if message.content == 'title':
                        a = await channel.send('タイトルを入力してください')
                        title = await self.bot.wait_for('message', check=check, timeout=300)
                        await title.delete()
                        embed.title = title.content
                        await a.delete()
                    elif message.content == 'desc':
                        a = await channel.send('説明を入力してください')
                        desc = await self.bot.wait_for('message', check=check, timeout=300)
                        await desc.delete()
                        embed.description = desc.content
                        await a.delete()
                    elif message.content == 'field':
                        a = await channel.send('フィールドを追加ヘルプを参考に入力してください')
                        field_help_embed = discord.Embed(
                            title='--フィールド追加ヘルプ--', description='フィールドを追加します\n名前の部分やフィールドの部分でNoneを送信するとなしにできます', color=0x00ff00)
                        field_help_embed.add_field(
                            name='フィールドの名前の部分', value='フィールドの文章の部分', inline=False)
                        await help_message.edit(embed=field_help_embed)
                        b = await channel.send('フィールドの名前を入力してください')
                        field_name = await self.bot.wait_for('message', check=check, timeout=300)
                        if field_name.content == 'None':
                            field_name.content = ''
                        c = await channel.send('フィールドの文章を入力してください')
                        field_value = await self.bot.wait_for('message', check=check, timeout=300)
                        if field_value.content == 'None':
                            field_value.content = ''
                        embed.add_field(name=field_name.content,
                                        value=field_value.content, inline=False)
                        await preview_message.edit(content='プレビューを編集しています...')
                        await a.delete()
                        await b.delete()
                        await field_name.delete()
                        await c.delete()
                        await field_value.delete()
                        await help_message.edit(embed=help_embed)
                        await preview_message.edit(content='プレビュー', embed=embed)
                    elif message.content == 'pic':
                        pic_help_embed = discord.Embed(
                            title='--写真追加ヘルプ--', description='写真を追加します\n追加するタイプを選び画像のurlを送信してください\nthumを送信すると右のようになります→\nimageを送信すると下のようになります↓', color=0x00ff00)
                        pic_help_embed.set_image(
                            url=f'{self.bot.get_user(814465495914119218).avatar.url}')
                        pic_help_embed.set_thumbnail(
                            url=f'{self.bot.get_user(814465495914119218).avatar.url}')
                        await help_message.edit(embed=pic_help_embed)
                        while True:
                            a = await channel.send('追加するタイプを選んでください\nthum or image')
                            pic_type = await self.bot.wait_for('message', check=check, timeout=300)
                            if pic_type.content == 'thum' or pic_type.content == 'image':
                                break
                            else:
                                await channel.send('thumかimageを入力してください')
                            await pic_type.delete()
                        b = await channel.send('画像のurlを送信してください')
                        pic_url = await self.bot.wait_for('message', check=check, timeout=300)
                        if pic_type.content == 'thum':
                            embed.set_thumbnail(url=pic_url.content)
                        elif pic_type.content == 'image':
                            embed.set_image(url=pic_url.content)
                        await a.delete()
                        await pic_type.delete()
                        await b.delete()
                        await pic_url.delete()
                        await preview_message.edit(embed=embed)
                        await help_message.edit(embed=help_embed)
                    elif message.content == 'color':
                        a = await channel.send('色を入力してください\n16進数で入力してください\n例:ffffff')
                        color = await self.bot.wait_for('message', check=check, timeout=300)
                        embed.color = int(color.content, 16)
                        await a.delete()
                        await color.delete()
                        await preview_message.edit(embed=embed)
                    elif message.content == 'time':
                        DIFF_JST_FROM_UTC = 9
                        jp_time = datetime.datetime.now(
                            datetime.timezone.utc)
                        embed.timestamp = jp_time
                        await preview_message.edit(embed=embed)
                    elif message.content == 'send':
                        await ctx.channel.send(embed=embed)
                        await channel.delete()
                        return
                    elif message.content == 'end':
                        await channel.delete()
                        return
                    else:
                        m = await channel.send('無効なコマンドです')
                        await asyncio.sleep(2)
                        await m.delete()
                        continue
                    await preview_message.edit(embed=embed)
                except asyncio.TimeoutError:
                    await channel.send(f'<@{ctx.user.id}>\nタイムアウトしました\nやり直してください\nチャンネルは10秒後に削除されます')
                    await asyncio.sleep(10)
                    await channel.delete()
                    return
        except discord.errors.NotFound:
            await ctx.response.send_message(content='エラーが発生しました', ephemeral=True)
            if channel is not None:
                await channel.delete()

    @commands.command()
    async def startlevel(self, ctx: commands.Context):
        if ctx.guild is None:
            await ctx.send(content='サーバー内で実行してください')
            return
        if ctx.author.guild_permissions.administrator:
            result = ServerLevels.create(guild_id=ctx.guild.id, channel_id=ctx.channel.id)
            if result == 0:
                await ctx.send(content='開始しました')
            else:
                await ctx.send(content='すでに開始されています', ephemeral=True)
        else:
            await ctx.send(content='権限がありません', ephemeral=True)

def divide_list(l, i) -> list:
    """リストをランダムに分割する
    Args:
        l (list): 分割したいリスト
        i (int): 分割する数
    """
    divided_list = [[] for _ in range(i)] # 分割後のリスト
    l_copy = l.copy() # 元のリストを変更しないためのコピー
    index = 0
    while l_copy:
        k = random.randint(0, len(l_copy)-1)
        divided_list[index].append(l_copy.pop(k))
        index = (index + 1) % i # indexがiに達したら0に戻す
    return divided_list


async def setup(bot):
    await bot.add_cog(General(bot))