import discord
from discord.ext import commands
from models import UserLevels, ServerLevels
from datetime import timezone, timedelta
from discord import app_commands



class Level(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def update_xp(self, message: discord.Message):
        level_channel_id = ServerLevels.get(guild_id=message.guild.id)
        if level_channel_id is None:
            return
        else:
            user_level = UserLevels.get(user_id=message.author.id, guild_id=message.guild.id)
            if user_level is None:
                UserLevels.create(user_id=message.author.id, guild_id=message.guild.id, level=1, xp=0, last_message=message.created_at)
                user_level = UserLevels.get(user_id=message.author.id, guild_id=message.guild.id)
            message_created_at = message.created_at
            last_message = user_level['last_message'].replace(tzinfo=timezone.utc) - timedelta(hours=9)
            if (message_created_at - last_message).seconds < 300:
                return
            user_level['xp'] += 1
            max_xp = user_level['level'] * 10
            if user_level['xp'] >= max_xp:
                user_level['level'] += 1
                user_level['xp'] = 0
                level_channel = self.bot.get_channel(level_channel_id['channel_id'])
                await level_channel.send(f'{message.author.mention} level up!  {user_level["level"]-1} -> {user_level["level"]}')
            UserLevels.update(id=user_level['id'],
                              user_id=user_level['user_id'],
                              guild_id=user_level['guild_id'],
                              level=user_level['level'],
                              xp=user_level['xp'],
                              last_message=message.created_at)

    @app_commands.command(name='level', description='レベルを表示します')
    async def level(self, ctx: discord.Interaction):
        user_level = UserLevels.get(user_id=ctx.user.id , guild_id=ctx.guild.id)
        if user_level is None:
            await ctx.response.send_message(content='レベルは1です')
        else:
            await ctx.response.send_message(content=f'レベルは{user_level["level"]}です')

    @app_commands.command(name='rank', description='ランキングを表示します')
    async def rank(self, ctx: discord.Interaction):
        user_levels = UserLevels.filter(guild_id=ctx.guild.id)
        user_levels.sort(key=lambda x: x['level'], reverse=True)
        rank = 1
        embed = discord.Embed(title='ランキング')
        for user_level in user_levels:
            user = self.bot.get_user(user_level['user_id'])
            embed.add_field(name=f'{rank}位', value=f'{user.mention} レベル: {user_level["level"]}', inline=False)
            rank += 1
        await ctx.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Level(bot))