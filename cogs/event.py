import discord
from discord.ext import commands
import random

from cogs import level

class Event(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.level = level.Level(self.bot)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # *botからのメッセージを無視
        if message.author.bot:
            return

        await self.level.update_xp(message)

        async def recruit_game(title, detail, max):
            embed = discord.Embed(title=title, description=detail, color=0x00ff00)
            name = f'参加者 (1/{max})'
            embed.add_field(
                name=name, value=f'<@{message.author.id}>', inline=False)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label='参加', style=discord.ButtonStyle.primary, custom_id="join"))
            view.add_item(discord.ui.Button(
                label='辞退', style=discord.ButtonStyle.primary, custom_id="cancel"))
            view.add_item(discord.ui.Button(
                label='終了', style=discord.ButtonStyle.red, custom_id="delete"))
            await message.channel.send(embed=embed, view=view)

        # *げーむ部サーバーのみの設定
        if message.guild is not None and message.guild.id == 785868785282318356:
            # *'!a'が送られたときapexの募集をかける
            if message.content == '!a':
                await message.channel.send(f'<@&{813388084423032862}>')
                await recruit_game('Apex', '', 3)
            if message.content == '!v':
                await message.channel.send(f'<@&{1116565656469520405}>')
                await recruit_game('Valorant', '', 5)
        # *管理者のみの設定
        if message.author.id == 785868066525020170:
            try:
                if '!test' == message.content:
                    # !テストしたい時ここに書く
                    pass
                if 'send all guild':
                    pass
                    # todo 全てのサーバーに埋め込みメッセージを送信(アップデート時に使用)
            except Exception as e:
                await message.channel.send(f'An error occurred: {e}')

    @commands.Cog.listener()
    async def on_button_click(self, ctx: discord.Interaction):
        def find_num(s: str) -> list:
            """募集人数を取得する
            Args:
                s (str): 募集内容
            Returns:
                list: [現在の参加人数, 募集人数]
            """
            start_index1 = s.find("/") + 1
            end_index1 = s.find(")")
            max_number = int(s[start_index1:end_index1])
            start_index2 = s.find("(") + 1
            end_index2 = s.find("/")
            number = int(s[start_index2:end_index2])
            return [number, max_number]

        custom_id = ctx.data['custom_id']
        message_id = ctx.message.id
        message = await ctx.channel.fetch_message(message_id)
        embed = message.embeds[0]
        embed_dict = embed.to_dict()
        member_str = embed_dict['fields'][0]['value']
        member_list = member_str.split('\n')
        name = embed_dict['fields'][0]['name']

        if custom_id == 'select':
            await ctx.response.defer(thinking=True)
            # print(embed_dict)
            result_str = ''
            for _ in range(int(embed_dict['description'])):
                selected_user = member_list.pop(random.randrange(0, len(member_list)))
                result_str += f'{selected_user}\n'
            result_embed = discord.Embed(title='結果', description=result_str, color=0x00ff00)
            await ctx.followup.send(embed=result_embed)
            return

        # --参加ボタンが押されたとき--
        if custom_id == 'join':
            # *すでに参加しているとき
            if f'<@{ctx.user.id}>' in member_list:
                await ctx.response.send_message(content=f'<@{ctx.user.id}> すでに参加しています', ephemeral=True)
                return
            # *参加してないとき
            member_str += f'\n<@{ctx.user.id}>'  # 参加者リストに追加
            # *募集人数が設定されているとき
            if '/' in name:
                num_list = find_num(name)  # 現在の参加人数と募集人数を取得
                num_now = num_list[0] + 1  # 現在の参加人数を更新
                num_max = num_list[1]  # 募集人数を取得
                name = f'参加者 ({num_now}/{num_max})'
                # *募集人数に達したとき
                if num_now == num_max:
                    view = discord.ui.View()
                    if '__' in ctx.channel.name:
                        view.add_item(discord.ui.Button(
                            label='アーカイブ', style=discord.ButtonStyle.red, custom_id="archive"))
                    embed.color = discord.Color.red()
                    embed.set_field_at(
                        0, name=name, value=member_str, inline=False)
                    await message.edit(embed=embed, view=view)
                    await ctx.response.send_message(content=f'\n募集内容:{embed.title}\n{member_str}')
                    # *ロールが設定されているとき
                    try:
                        role_id = embed_dict['fields'][1]['value'].split('&')[
                            1].replace('>', '')
                        role = ctx.guild.get_role(int(role_id))
                        await role.delete()
                    except:
                        pass
                    return
            else:
                # *人数が0から1になるとき　len(member_list) + 1 は2になってしまうのでその処理
                if len(member_list) == 1 and member_list[0] == '':
                    name = f'参加者 (1)'
                else:
                    # 参加者数を更新 リストの長さは参加者数より1少ない
                    name = f'参加者 ({len(member_list) + 1})'
            embed.set_field_at(0, name=name, value=member_str, inline=False)
            await message.edit(embed=embed)  # メッセージを更新
            # *ロールが設定されているとき
            try:
                role_id = embed_dict['fields'][1]['value'].split('&')[
                    1].replace('>', '')
                role = ctx.guild.get_role(int(role_id))
                await ctx.user.add_roles(role)
            except:
                pass
            await ctx.response.send_message(content=f'<@{ctx.user.id}> 参加しました', ephemeral=True)

        # --辞退ボタンが押されたとき--
        if custom_id == 'cancel':
            # *参加していないとき
            if f'<@{ctx.user.id}>' not in member_list:
                await ctx.response.send_message(content=f'<@{ctx.user.id}> まだ参加していません', ephemeral=True)
                return
            # *参加しているとき
            member_list.remove(f'<@{ctx.user.id}>')  # 参加者リストから削除
            member_str = '\n'.join(member_list)
            # *募集人数が設定されているとき
            if '/' in name:
                num_list = find_num(name)
                num_now = num_list[0] - 1
                num_max = num_list[1]
                name = f'参加者 ({num_now}/{num_max})'
            else:
                name = f'参加者 ({len(member_list)})'  # 参加者数を更新 リストの長さはすでに1引かれている
            embed.set_field_at(0, name=name, value=member_str, inline=False)
            await message.edit(embed=embed)
            # *ロールが設定されているとき
            try:
                role_id = embed_dict['fields'][1]['value'].split('&')[
                    1].replace('>', '')
                role = ctx.guild.get_role(int(role_id))
                await ctx.user.remove_roles(role)
            except:
                pass
            await ctx.response.send_message(content=f'<@{ctx.user.id}> 辞退しました', ephemeral=True)

        # --終了ボタンが押されたとき--
        if custom_id == 'delete':
            # *ボタンを押した人が募集者かオーナーのとき
            if f'<@{ctx.user.id}>' == member_list[0] or ctx.user.id == ctx.guild.owner.id:
                # *ロールが設定されているとき
                try:
                    role_id = embed_dict['fields'][1]['value'].split('&')[
                        1].replace('>', '')
                    role = ctx.guild.get_role(int(role_id))
                    await role.delete()
                except:
                    pass
                embed.color = discord.Color.red()
                view = discord.ui.View()
                if '__' in ctx.channel.name:
                    view.add_item(discord.ui.Button(
                        label='アーカイブ', style=discord.ButtonStyle.red, custom_id="archive"))
                await message.edit(embed=embed, view=view)
                await ctx.response.send_message(content=f'募集を終了しました\n募集内容:{embed.title}\n{member_str}', ephemeral=False)
            # *募集者でもオーナーでもないとき
            else:
                await ctx.response.send_message(content='募集者のみが募集を終了できます', ephemeral=True)

        # --再送ボタンが押されたとき--
        if custom_id == 'resend':
            # *ボタンを押した人が募集者かオーナーのとき
            if f'<@{ctx.user.id}>' == member_list[0] or ctx.user.id == ctx.guild.owner.id:
                view = discord.ui.View()
                view.add_item(discord.ui.Button(
                    label='参加', style=discord.ButtonStyle.primary, custom_id="join"))
                view.add_item(discord.ui.Button(
                    label='辞退', style=discord.ButtonStyle.primary, custom_id="cancel"))
                view.add_item(discord.ui.Button(
                    label='終了', style=discord.ButtonStyle.red, custom_id="delete"))
                view.add_item(discord.ui.Button(
                    label='再送', style=discord.ButtonStyle.green, custom_id="resend"))
                await ctx.response.send_message(embed=embed, view=view)
                await message.delete()
            # *募集者でもオーナーでもないとき
            else:
                await ctx.response.send_message(content='募集者のみが募集を再送できます', ephemeral=True)

        # --チャンネル削除ボタンが押されたとき--
        if custom_id == 'archive':
            # *ボタンを押した人が募集者かオーナーのとき
            if f'<@{ctx.user.id}>' == member_list[0] or ctx.user.id == ctx.guild.owner.id:
                view = discord.ui.View()
                await message.edit(embed=embed, view=view)
                for category in ctx.guild.categories:
                    if category.name == 'archive':
                        await ctx.channel.edit(category=category)
                        await ctx.response.send_message(content='チャンネルをアーカイブに移動しました', ephemeral=False)
                        return
                category = await ctx.guild.create_category_channel(name='archive')
                await ctx.channel.edit(category=category)
                await ctx.response.send_message(content='チャンネルをアーカイブに移動しました', ephemeral=False)
            # *募集者でもオーナーでもないとき
            else:
                await ctx.response.send_message(content='募集者のみがチャンネルを削除できます', ephemeral=True)

    # ボイスステートが変更されたときの処理
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        # *'##'が名前についたVCから全員が退出したときVCを削除
        try:
            if before.channel is not None and '##' in before.channel.name and len(before.channel.members) == 0:
                await before.channel.delete()
        except:
            pass

        # *-create vc-が名前についたVCに入ったとき新しいVCを作成し移動
        try:
            if '-create vc-' in after.channel.name:
                category = after.channel.category
                voice_channel = await category.create_voice_channel(name=f'##VC##')
                for member in after.channel.members:
                    await member.move_to(voice_channel)
        except:
            pass

        # *VCに入室したときVC-logに通知
        try:
            if before.channel is None and len(after.channel.members) == 1:
                voice_channel: discord.VoiceChannel = after.channel
                channels = voice_channel.guild.channels
                for channel in channels:
                    if 'vc-log' in channel.name:
                            await channel.send(f'{voice_channel.mention} に {member.display_name} が入室しました')
        except:
            # await kushina.send(f'An error occurred:')
            pass

    # セレクトが選択されたときの処理
    async def on_select(self, ctx: discord.Interaction) -> None:
        custom_id = ctx.data['values'][0]
        print(custom_id)
        # *チーム分けコマンドのヘルプ
        if custom_id == '/team':
            embed_team = discord.Embed(
                title='ようせいさん-help', description='', color=0x87ceeb)
            embed_team.add_field(
                name='>> /team num_team: exclude_member: auto:', value='', inline=False)
            embed_team.add_field(
                name='VCに入っているメンバーをランダムにチーム分けします', value='', inline=False)
            embed_team.add_field(name='num_team', value='チーム数', inline=False)
            embed_team.add_field(name='exclude_member',
                                value='除外するメンバー', inline=False)
            embed_team.add_field(
                name='auto', value='チーム分け後に自動でVCを移動するかどうか\n何かしら入力されてたら今いるVCのすぐ下にチームVCが作成され、自動で送られます\nVCは全員抜けると削除されます', inline=False)
            await ctx.response.edit_message(embed=embed_team)
        # *ダイスコマンドのヘルプ
        if custom_id == '/dice':
            embed_dice = discord.Embed(
                title='ようせいさん-help', description='', color=0x87ceeb)
            embed_dice.add_field(name='>> /dice num:', value='', inline=False)
            embed_dice.add_field(name='ダイスを振ります', value='', inline=False)
            embed_dice.add_field(name='num', value='ダイスの個数', inline=False)
            await ctx.response.edit_message(embed=embed_dice)
        # *募集コマンドのヘルプ
        if custom_id == '/r':
            embed_r = discord.Embed(title='ようせいさん-help',
                                    description='', color=0x87ceeb)
            embed_r.add_field(
                name='>> /r title: detail: max: role:', value='', inline=False)
            embed_r.add_field(name='募集を行います', value='', inline=False)
            embed_r.add_field(name='title', value='募集タイトル', inline=False)
            embed_r.add_field(name='detail', value='募集内容', inline=False)
            embed_r.add_field(name='max', value='募集人数', inline=False)
            embed_r.add_field(
                name='role', value='付与するロール\n付与されたロールは募集が終了したら削除されます', inline=False)
            await ctx.response.edit_message(embed=embed_r)
        # *VC名変更コマンドのヘルプ
        if custom_id == '/vc':
            embed_vc = discord.Embed(title='ようせいさん-help',
                                    description='', color=0x87ceeb)
            embed_vc.add_field(name='>> /vc name:', value='', inline=False)
            embed_vc.add_field(
                name='VC名を変更します\nbotによって作成された"##"ではじまるVCの名前のみ変更できます', value='', inline=False)
            embed_vc.add_field(name='name', value='変更後のVC名', inline=False)
            await ctx.response.edit_message(embed=embed_vc)
        # *twitch登録コマンドのヘルプ
        if custom_id == '/twitch':
            embed_twitch = discord.Embed(
                title='ようせいさん-help', description='', color=0x87ceeb)
            embed_twitch.add_field(
                name='>> /twitch twitch_name:', value='', inline=False)
            embed_twitch.add_field(
                name='twitchの通知を登録します\nコマンドが送信されたチャンネルに配信開始通知が送信されます', value='', inline=False)
            embed_twitch.add_field(
                name='twitch_name', value='twitchのユーザーネーム', inline=False)
            await ctx.response.edit_message(embed=embed_twitch)
        # *twitch解除コマンドのヘルプ
        if custom_id == '/del_twitch':
            embed_del_twitch = discord.Embed(
                title='ようせいさん-help', description='', color=0x87ceeb)
            embed_del_twitch.add_field(
                name='>> /del_twitch twitch_name:', value='', inline=False)
            embed_del_twitch.add_field(
                name='チャンネルに登録されたtwitchの通知を解除します', value='', inline=False)
            embed_del_twitch.add_field(
                name='twitch_name', value='twitchのユーザーネーム', inline=False)
            await ctx.response.edit_message(embed=embed_del_twitch)
        # *twitch登録確認コマンドのヘルプ
        if custom_id == '/check_twitch':
            embed_check_twitch = discord.Embed(
                title='ようせいさん-help', description='', color=0x87ceeb)
            embed_check_twitch.add_field(
                name='>> /check_twitch', value='', inline=False)
            embed_check_twitch.add_field(
                name='チャンネルに登録されたtwitchを確認します', value='', inline=False)
            await ctx.response.edit_message(embed=embed_check_twitch)
        # *誕生日登録コマンドのヘルプ
        if custom_id == '/birthday':
            embed_birthday = discord.Embed(
                title='ようせいさん-help', description='', color=0x87ceeb)
            embed_birthday.add_field(
                name='>> /birthday user: birthday:', value='', inline=False)
            embed_birthday.add_field(
                name='誕生日を登録します\n誕生日になると登録したチャンネルで通知します', value='', inline=False)
            embed_birthday.add_field(
                name='user', value='ユーザー(メンション)', inline=False)
            embed_birthday.add_field(name='birthday', value='誕生日', inline=False)
            await ctx.response.edit_message(embed=embed_birthday)
        # *誕生日解除コマンドのヘルプ
        if custom_id == '/del_birthday':
            embed_del_birthday = discord.Embed(
                title='ようせいさん-help', description='', color=0x87ceeb)
            embed_del_birthday.add_field(
                name='>> /del_birthday user:', value='', inline=False)
            embed_del_birthday.add_field(
                name='チャンネルに登録された誕生日を解除します', value='', inline=False)
            embed_del_birthday.add_field(name='user', value='ユーザー', inline=False)
            await ctx.response.edit_message(embed=embed_del_birthday)
        # *誕生日確認コマンドのヘルプ
        if custom_id == '/check_birthday':
            embed_check_birthday = discord.Embed(
                title='ようせいさん-help', description='', color=0x87ceeb)
            embed_check_birthday.add_field(
                name='>> /check_birthday', value='', inline=False)
            embed_check_birthday.add_field(
                name='チャンネルに登録されている誕生日を確認します', value='', inline=False)
            await ctx.response.edit_message(embed=embed_check_birthday)

    async def on_user_select(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True, ephemeral=True)
        message_id = ctx.message.id
        message = await ctx.channel.fetch_message(message_id)
        embed = message.embeds[0]
        embed_dict = embed.to_dict()
        name = embed_dict['fields'][0]['name']
        users = ''
        for user in ctx.data['values']:
            users += f'<@{user}>\n'
        embed.set_field_at(0, name=name, value=users, inline=False)
        await message.edit(embed=embed)
        await ctx.followup.send(content='更新しました', ephemeral=True)

    # インタラクションの中からボタンのクリックとセレクトを選別
    @commands.Cog.listener()
    async def on_interaction(self, ctx: discord.Interaction) -> None:
        try:
            if ctx.data['component_type'] == 2:
                await self.on_button_click(ctx)
            if ctx.data['component_type'] == 3:
                await self.on_select(ctx)
            if ctx.data['component_type'] == 5:
                await self.on_user_select(ctx)
        except KeyError:
            pass

async def setup(bot):
    await bot.add_cog(Event(bot))