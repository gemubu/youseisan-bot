import discord
from discord.ext import commands
from discord import app_commands
from google.cloud import texttospeech
import re
import asyncio

# todo
"""
サーバーごとに文字数をカウント，1ヶ月で1万文字以上は送れないように
参加時と切断時に現在の使用した文字数を表示
設定で声を変えたり，言語を変えたりできるようにしたい
起動時にapiで設定を呼んで辞書に入れる
"""


class Tts(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

        self.client = texttospeech.TextToSpeechClient()

        # 出力する音声のフォーマットを設定
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16 # wav
        )

        self.active_channel: dict[int, int] = {}
        self.voice_settings: dict[int, dict] = {}
        # 各サーバーの読み上げキュー
        self.guild_queues: dict[int, asyncio.Queue] = {}
        # 再生ループを動かすためのタスク
        self.play_tasks: dict[int, asyncio.Task] = {}


    @commands.Cog.listener()
    async def on_ready(self) -> None:
        for vc in self.bot.voice_clients:
            await vc.disconnect(force=True)


    @app_commands.command(name='join', description='読み上げを開始するためにVCに接続します')
    async def join(self, ctx: discord.Interaction):
        # コマンドを実行したユーザーのVC参加状況を確認
        if ctx.user.voice is None or ctx.user.voice.channel is None:
            await ctx.response.send_message("ボイスチャンネルに参加してから実行してください。", ephemeral=True)
            return

        channel = ctx.user.voice.channel

        # 既に接続している場合はメッセージを出す
        if ctx.guild.voice_client is not None:
            await ctx.response.send_message("すでにボイスチャンネルに接続しています。", ephemeral=True)
            return

        voice_channel = ctx.user.voice.channel
        try:
            # todo 現在の設定と，今月の使用した文字数，設定するためのサイトへ飛ぶリンクを埋め込みで送信
            await voice_channel.connect(reconnect=False)
            await ctx.response.send_message(f"{channel.name} に接続しました。")
            self.active_channel[ctx.guild.id] = ctx.channel.id
            self.voice_settings[ctx.channel.id] = {"language":"ja-JP", "voice":"ja-JP-Neural2-C", "char_count":0}

            # サーバー専用の再生キューを作成
            self.guild_queues[ctx.guild.id] = asyncio.Queue()

            # 再生ループを開始（別タスクで動かす）
            self.play_tasks[ctx.guild.id] = asyncio.create_task(self.play_audio_loop(ctx.guild))

        except Exception as e:
            await ctx.response.send_message(f"ボイスチャンネルへ接続できませんでした: {e}", ephemeral=True)
            return


    @app_commands.command(name="leave", description="ボイスチャンネルから切断し，読み上げを停止します。")
    async def leave(self, ctx: discord.Interaction):
        guild = ctx.guild
        if guild is None:
            await ctx.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return

        vc = guild.voice_client
        if vc is None or not vc.is_connected():
            await ctx.response.send_message("接続していません。", ephemeral=True)
            return

        if ctx.channel.id == self.active_channel[ctx.guild.id]:
            self.active_channel.pop(guild.id, None)

            # 再生タスクをキャンセル
            if guild.id in self.play_tasks:
                self.play_tasks[guild.id].cancel()
                self.play_tasks.pop(guild.id, None)

            await vc.disconnect(force=True)
            # todo 今回使用した文字数と今月何文字使ってるかを埋め込みで送信する
            await ctx.response.send_message("切断しました。読み上げを停止しました。")
        else:
            await ctx.response.send_message("読み上げを開始したチャンネルで実行してください")


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        guild_id = message.guild.id
        if guild_id not in self.active_channel:
            return
        if message.channel.id != self.active_channel[guild_id]:
            return

        # 絵文字削除
        custom_emoji_pattern = re.compile(r'<a?:\w+:\d+>')
        message.content = re.sub(custom_emoji_pattern, '', message.content)
        if not message.content.strip():
            return

        # テキストをキューに追加
        await self.guild_queues[guild_id].put((message.channel, message.content))



    async def play_audio_loop(self, guild: discord.Guild):
        """各サーバーごとにメッセージを順番に読み上げるループ"""
        vc = guild.voice_client
        queue = self.guild_queues[guild.id]
        settings = self.voice_settings[self.active_channel[guild.id]]

        while True:
            try:
                channel, text = await queue.get()

                # テキストを音声に変換
                synthesis_input = texttospeech.SynthesisInput(text=text)
                voice = texttospeech.VoiceSelectionParams(
                    language_code=settings["language"],
                    name=settings["voice"],
                )
                response = self.client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=self.audio_config
                )

                filename = f"{guild.id}.wav"
                with open(filename, "wb") as out:
                    out.write(response.audio_content)

                # 再生中なら待機
                while vc.is_playing():
                    await asyncio.sleep(0.2)

                vc.play(discord.FFmpegPCMAudio(filename))
                await asyncio.sleep(1)  # 音声再生が始まるまで少し待つ
                while vc.is_playing():
                    await asyncio.sleep(0.5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(1)


    # vcからbot以外の全てのメンバーがいなくなった時,VCから切断する
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if before.channel is not None:
            try:
                guild = before.channel.guild
                if len(before.channel.members) and before.channel.members[0].id == self.bot.user.id and len(before.channel.members) == 1:
                    await before.channel.send("自動でVCから切断しました。")
                    vc = guild.voice_client
                    self.active_channel.pop(guild.id, None)
                    if guild.id in self.play_tasks:
                        self.play_tasks[guild.id].cancel()
                        self.play_tasks.pop(guild.id, None)
                    await vc.disconnect()
            except Exception as e:
                print(e)
                pass

            try:
                if len(before.channel.members) and member.id == self.bot.user.id and after.channel == None:
                    guild = before.channel.guild
                    await before.channel.send("VCから切断されたため読み上げを停止します。")
                    self.active_channel.pop(before.channel.guild.id, None)
                    if guild.id in self.play_tasks:
                        self.play_tasks[guild.id].cancel()
                        self.play_tasks.pop(guild.id, None)
            except Exception as e:
                print(e)
                pass


async def setup(bot):
    await bot.add_cog(Tts(bot))