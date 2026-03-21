"""Discord bot: CluesBySam messages → Google Sheets."""

from __future__ import annotations

import asyncio
import logging
import os

import discord

from cbs_parser import is_clues_by_sam_attempt, parse_clues_by_sam
from sheets_client import append_score_row, sheet_has_row_for_day_and_name

log = logging.getLogger(__name__)


def _sheets_dry_run() -> bool:
    v = (
        os.environ.get("CBSC_SHEETS_DRY_RUN", os.environ.get("SHEETS_DRY_RUN", ""))
        .strip()
        .lower()
    )
    return v in ("1", "true", "yes", "on")


def _sheet_dedupe_enabled() -> bool:
    """Skip append when the sheet already has the same Day (A) + Name (B). On by default."""
    v = os.environ.get("CBSC_DEDUPE_SHEET", "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def _allowed_channels() -> set[int] | None:
    raw = os.environ.get("ALLOWED_CHANNEL_IDS", "").strip()
    if not raw:
        return None
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def _allowed_guilds() -> set[int] | None:
    raw = os.environ.get("ALLOWED_GUILD_IDS", "").strip()
    if not raw:
        return None
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def _build_client() -> discord.Client:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    intents.messages = True
    return discord.Client(intents=intents)


async def send_error_in_thread(message: discord.Message, body: str) -> None:
    try:
        if message.thread is not None:
            await message.thread.send(body)
            return
        thread = await message.create_thread(
            name="CluesBySam",
            auto_archive_duration=1440,
        )
        await thread.send(body)
    except (discord.Forbidden, discord.HTTPException) as e:
        log.warning("Thread error path failed: %s", e)
        try:
            await message.reply(body, mention_author=False)
        except (discord.Forbidden, discord.HTTPException):
            log.exception("Could not reply with error")


def run_bot() -> None:
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is not set.")

    allowed_channels = _allowed_channels()
    allowed_guilds = _allowed_guilds()
    client = _build_client()

    @client.event
    async def on_ready() -> None:
        log.info("Logged in as %s (%s)", client.user, client.user.id if client.user else "?")

    @client.event
    async def on_message(message: discord.Message) -> None:
        if message.author.bot:
            return
        if allowed_guilds is not None:
            if message.guild is None or message.guild.id not in allowed_guilds:
                return
        if allowed_channels is not None and message.channel.id not in allowed_channels:
            return

        content = message.content or ""
        if not is_clues_by_sam_attempt(content):
            return

        display_name = message.author.display_name

        try:
            parsed = parse_clues_by_sam(content)
        except ValueError as e:
            await send_error_in_thread(message, f"Couldn’t read your score — {e}")
            return

        if _sheet_dedupe_enabled():
            try:
                exists = await asyncio.to_thread(
                    sheet_has_row_for_day_and_name,
                    day=parsed.day,
                    name=display_name,
                )
            except Exception:
                log.exception("Sheet dedupe read failed")
                await send_error_in_thread(
                    message,
                    "Couldn’t check the sheet for duplicates — please try again or ask an admin to check the bot logs.",
                )
                return
            if exists:
                log.info(
                    "Ignoring duplicate score (sheet already has day=%r name=%r)",
                    parsed.day,
                    display_name,
                )
                return

        if _sheets_dry_run():
            print("--- CluesBySam (Sheets dry run) ---", flush=True)
            print(f"raw: {content!r}", flush=True)
            print(
                "parsed:",
                {
                    "day": parsed.day,
                    "name": display_name,
                    "difficulty": parsed.difficulty,
                    "time": parsed.time,
                    "perfect": parsed.perfect,
                    "hints": parsed.hints,
                },
                flush=True,
            )
            print("---", flush=True)
        else:
            try:
                await asyncio.to_thread(
                    append_score_row,
                    day=parsed.day,
                    name=display_name,
                    difficulty=parsed.difficulty,
                    time=parsed.time,
                    perfect=parsed.perfect,
                    hints=parsed.hints,
                )
            except Exception:
                log.exception("Sheets append failed")
                await send_error_in_thread(
                    message,
                    "Couldn’t save to the sheet — please try again or ask an admin to check the bot logs.",
                )
                return

        try:
            await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        except (discord.Forbidden, discord.HTTPException):
            log.warning("Could not add reaction to message %s", message.id)

    client.run(token)
