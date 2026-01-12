# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
import os
import json
import base64
import logging

from utils import temp
from pyrogram import Client, filters, enums
from pyrogram.errors import MessageNotModified
from pyrogram.errors.exceptions.bad_request_400 import (
    ChannelInvalid,
    UsernameInvalid,
    UsernameNotModified
)

from info import ADMINS, LOG_CHANNEL, FILE_STORE_CHANNEL
from database.ia_filterdb import unpack_new_file_id

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# -------------------- SECURITY: ADMIN ONLY --------------------

async def admin_only(_, __, message):
    if not message.from_user:
        return False
    if message.from_user.id in ADMINS:
        return True
    await message.reply("❌ This command is for admins only.")
    return False


# -------------------- SINGLE LINK --------------------

@Client.on_message(filters.command(["link", "plink"]) & filters.create(admin_only))
async def gen_link_s(bot, message):

    try:
        vj = await bot.ask(
            chat_id=message.from_user.id,
            text="Now Send Me Your Message Which You Want To Store.",
            timeout=60
        )
    except Exception:
        return await message.reply("⏳ Timeout! Send the command again.")

    file_type = vj.media

    if file_type not in (
        enums.MessageMediaType.VIDEO,
        enums.MessageMediaType.AUDIO,
        enums.MessageMediaType.DOCUMENT
    ):
        return await vj.reply("Send only Video / Audio / Document.")

    # Security: Block protected content
    if vj.has_protected_content:
        return await vj.reply("❌ Protected content is not allowed.")

    try:
        file_id = unpack_new_file_id(
            getattr(vj, file_type.value).file_id
        )[0]
    except Exception:
        return await vj.reply("❌ Failed to process this file.")

    string = "filep_" if message.text.lower().strip() == "/plink" else "file_"
    string += file_id

    outstr = base64.urlsafe_b64encode(
        string.encode("ascii")
    ).decode().strip("=")

    await message.reply(
        f"Here is your link:\n"
        f"https://t.me/{temp.U_NAME}?start={outstr}"
    )


# -------------------- BATCH LINK --------------------

@Client.on_message(filters.command(["batch", "pbatch"]) & filters.create(admin_only))
async def gen_link_batch(bot, message):

    if " " not in message.text:
        return await message.reply(
            "Use correct format.\n"
            "<code>/batch https://t.me/VJ_Botz/10 https://t.me/VJ_Botz/20</code>"
        )

    parts = message.text.strip().split()
    if len(parts) != 3:
        return await message.reply("❌ Invalid format.")

    cmd, first, last = parts

    regex = re.compile(
        r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?([\w\d_]+)/(\d+)$"
    )

    match = regex.match(first)
    if not match:
        return await message.reply("❌ Invalid first link")

    f_chat_id = match.group(4)
    f_msg_id = int(match.group(5))

    if f_chat_id.isnumeric():
        f_chat_id = int("-100" + f_chat_id)

    match = regex.match(last)
    if not match:
        return await message.reply("❌ Invalid last link")

    l_chat_id = match.group(4)
    l_msg_id = int(match.group(5))

    if l_chat_id.isnumeric():
        l_chat_id = int("-100" + l_chat_id)

    if f_chat_id != l_chat_id:
        return await message.reply("❌ Chat IDs do not match.")

    try:
        chat_id = (await bot.get_chat(f_chat_id)).id
    except ChannelInvalid:
        return await message.reply("❌ Private channel. Make me admin first.")
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply("❌ Invalid link.")
    except Exception:
        return await message.reply("❌ Failed to access chat.")

    sts = await message.reply("Generating link... Please wait.")

    # File store mode
    if chat_id in FILE_STORE_CHANNEL:
        string = f"{f_msg_id}_{l_msg_id}_{chat_id}_{cmd.lower().strip()}"
        b64 = base64.urlsafe_b64encode(
            string.encode("ascii")
        ).decode().strip("=")

        try:
            await sts.edit(
                f"Here is your link:\n"
                f"https://t.me/{temp.U_NAME}?start=DSTORE-{b64}"
            )
        except MessageNotModified:
            pass
        return

    outlist = []
    og_msg = 0

    async for msg in bot.iter_messages(f_chat_id, l_msg_id, f_msg_id):
        if msg.empty or msg.service or not msg.media:
            continue

        try:
            file_type = msg.media
            file = getattr(msg, file_type.value)

            caption = msg.caption.html if msg.caption else ""

            outlist.append({
                "file_id": file.file_id,
                "caption": caption,
                "title": getattr(file, "file_name", ""),
                "size": file.file_size,
                "protect": cmd.lower().strip() == "/pbatch",
            })

            og_msg += 1

        except Exception:
            continue

    json_file = f"batchmode_{message.from_user.id}.json"

    try:
        with open(json_file, "w+") as f:
            json.dump(outlist, f)

        post = await bot.send_document(
            LOG_CHANNEL,
            json_file,
            file_name="Batch.json",
            caption="⚠️ Generated for filestore."
        )

        file_id = unpack_new_file_id(post.document.file_id)[0]

    finally:
        if os.path.exists(json_file):
            os.remove(json_file)

    try:
        await sts.edit(
            f"Here is your link:\n"
            f"Contains `{og_msg}` files.\n"
            f"https://t.me/{temp.U_NAME}?start=BATCH-{file_id}"
        )
    except MessageNotModified:
        pass
