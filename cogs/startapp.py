import asyncio
import logging
import os
from typing import Optional

import aiohttp
import discord
from discord.ext import commands


class StartApp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        # Bot参照と同期処理で使う設定・ステートを用意
        self.bot = bot
        self.base_url = os.getenv("BACKEND_API_BASE_URL", "http://django:8000")
        self.api_token = os.getenv("BACKEND_BOT_TOKEN")
        self.logger = logging.getLogger(__name__)
        self._sync_lock = asyncio.Lock()
        self._synced = False
        self._sync_task: Optional[asyncio.Task] = None
        self._timeout = aiohttp.ClientTimeout(total=60)

    def cog_unload(self) -> None:
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        # Botが起動したタイミングで一度だけ同期タスクを起動
        if self._synced:
            return
        if self._sync_task and not self._sync_task.done():
            return
        self._sync_task = asyncio.create_task(self._initial_sync())

    async def _initial_sync(self) -> None:
        try:
            await self.bot.wait_until_ready()
            async with self._sync_lock:
                if self._synced:
                    return
                if not self.api_token:
                    self.logger.warning(
                        "BACKEND_BOT_TOKEN is not set. Skipping backend sync."
                    )
                    return
                await self._sync_backend_state()
                self._synced = True
        except Exception:
            self.logger.exception("Failed to synchronize backend state on startup.")
        finally:
            self._sync_task = None

    async def _sync_backend_state(self) -> None:
        # 参加している全ギルドに対してギルド情報・メンバー情報を同期
        headers = {"Authorization": f"Bot {self.api_token}"}
        async with aiohttp.ClientSession(
            base_url=self.base_url.rstrip("/"),
            headers=headers,
            timeout=self._timeout,
        ) as session:
            for guild in self.bot.guilds:
                owner = await self._resolve_owner(guild)
                if owner:
                    await self._upsert_user(session, owner)
                await self._upsert_guild(session, guild, owner_id=owner.id if owner else None)
                await self._sync_guild_members(session, guild)
                await self._sync_bot_membership(session, guild.id)

    async def _resolve_owner(self, guild: discord.Guild) -> Optional[discord.abc.User]:
        # ownerが取得できないケースもあるので段階的に探索
        owner = guild.owner
        if owner:
            return owner
        owner = guild.get_member(guild.owner_id)
        if owner:
            return owner
        try:
            return await guild.fetch_member(guild.owner_id)
        except (discord.NotFound, discord.HTTPException):
            self.logger.warning("Failed to fetch owner for guild %s", guild.id)
            return None

    async def _sync_guild_members(self, session: aiohttp.ClientSession, guild: discord.Guild) -> None:
        # chunk/fetchでメンバー一覧を揃えてBot以外を同期
        if not guild.chunked:
            try:
                await guild.chunk()
            except (discord.HTTPException, discord.ClientException):
                self.logger.warning("Failed to chunk members for guild %s", guild.id)
        members = guild.members
        if not members:
            try:
                async for member in guild.fetch_members(limit=None):
                    if member.bot:
                        continue
                    await self._sync_member(session, guild.id, member)
            except (discord.HTTPException, discord.Forbidden):
                self.logger.warning("Failed to fetch members for guild %s", guild.id)
            return
        for member in members:
            if member.bot:
                continue
            await self._sync_member(session, guild.id, member)

    async def _sync_member(
        self,
        session: aiohttp.ClientSession,
        guild_id: int,
        member: discord.Member,
    ) -> None:
        # 各メンバーをバックエンド上のユーザー＋参加情報として upsert
        await self._upsert_user(session, member)
        await self._ensure_user_guild(session, guild_id, member.id)

    async def _sync_bot_membership(
        self,
        session: aiohttp.ClientSession,
        guild_id: int,
    ) -> None:
        # Bot自身も参加メンバーとして登録する
        bot_user = self.bot.user
        if bot_user is None:
            return
        await self._upsert_user(session, bot_user)
        await self._ensure_user_guild(session, guild_id, bot_user.id)

    async def _upsert_user(self, session: aiohttp.ClientSession, user: discord.abc.User) -> None:
        patch_payload = self._build_user_payload(user, include_id=False)
        create_payload = self._build_user_payload(user, include_id=True)
        patch_path = f"/account/users/{user.id}/"
        if await self._patch(session, patch_path, patch_payload):
            return
        await self._post(session, "/account/users/", create_payload)

    async def _upsert_guild(
        self,
        session: aiohttp.ClientSession,
        guild: discord.Guild,
        owner_id: Optional[int] = None,
    ) -> None:
        patch_payload = self._build_guild_payload(guild, owner_id, include_id=False)
        create_payload = self._build_guild_payload(guild, owner_id, include_id=True)
        patch_path = f"/guilds/{guild.id}/"
        if await self._patch(session, patch_path, patch_payload):
            return
        await self._post(session, "/guilds/", create_payload)

    async def _ensure_user_guild(
        self,
        session: aiohttp.ClientSession,
        guild_id: int,
        user_id: int,
    ) -> None:
        params = {"user": user_id, "guild": guild_id}
        # body を空で送るとバックエンド側で level/xp が初期化される
        async with session.post("/guilds/levels/", params=params, json={}) as resp:
            if resp.status in (200, 201, 204):
                return
            text = await resp.text()
            if resp.status == 400 and "already" in text.lower():
                return
            self.logger.error(
                "Failed to sync membership for guild %s user %s: %s %s",
                guild_id,
                user_id,
                resp.status,
                text,
            )

    async def _patch(
        self,
        session: aiohttp.ClientSession,
        path: str,
        payload: dict,
    ) -> bool:
        async with session.patch(path, json=payload) as resp:
            if resp.status in (200, 204):
                return True
            if resp.status != 404:
                text = await resp.text()
                self.logger.error("PATCH %s failed: %s %s", path, resp.status, text)
            return False

    async def _post(
        self,
        session: aiohttp.ClientSession,
        path: str,
        payload: dict,
    ) -> None:
        async with session.post(path, json=payload) as resp:
            if resp.status in (200, 201):
                return
            text = await resp.text()
            self.logger.error("POST %s failed: %s %s", path, resp.status, text)

    @staticmethod
    def _build_user_payload(
        user: discord.abc.User,
        include_id: bool = False,
    ) -> dict:
        avatar = getattr(getattr(user, "display_avatar", None), "url", None)
        payload = {
            "username": user.name,
            "global_name": getattr(user, "global_name", None),
            "avatar": str(avatar) if avatar else None,
        }
        if include_id:
            payload["discord_id"] = user.id
        return payload

    @staticmethod
    def _build_guild_payload(
        guild: discord.Guild,
        owner_id: Optional[int],
        include_id: bool = False,
    ) -> dict:
        icon = str(guild.icon.url) if guild.icon else None
        payload = {
            "name": guild.name,
            "icon": icon,
        }
        if owner_id:
            payload["owner"] = owner_id
        if include_id:
            payload["discord_id"] = guild.id
        return payload


async def setup(bot: commands.Bot):
    await bot.add_cog(StartApp(bot))
