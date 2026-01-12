# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re, os, json, base64, logging
from utils import temp
from pyrogram import filters, Client, enums
from pyrogram.errors.exceptions.bad_request_400 import (
    ChannelInvalid, UsernameInvalid, UsernameNotModified
)
from info import ADMINS, LOG_CHANNEL, FILE_STORE_CHANNEL, PUBLIC_FILE_STORE
from database.ia_filterdb import unpack_new_file_id

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def allowed(_, __, message):
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False


# ───────────────────────────────
# 🔹 SINGLE FILE LINK
# ───────────────────────────────
@Client.on_message(filters.command(['link', 'plink']) & filters.create(allowed))
async def gen_link_s(bot, message):
    vj = await bot.ask(
        chat_id=message.from_user.id,
        text="Now Send Me Your Message Which You Want To Store."
    )

    file_type = vj.media
    if file_type not in (
        enums.MessageMediaType.VIDEO,
        enums.MessageMediaType.AUDIO,
        enums.MessageMediaType.DOCUMENT
    ):
        return await vj.reply("Send me only video, audio or document.")

    if vj.has_protected_content and message.from_user.id not in ADMINS:
        return await vj.reply("This content is protected.")

    media = getattr(vj, file_type.value)
    file_id, _ = unpack_new_file_id(media.file_id)

    prefix = "filep_" if message.text.lower().strip() == "/plink" else "file_"
    payload = prefix + file_id

    encoded = base64.urlsafe_b64encode(
        payload.encode("ascii")
    ).decode().rstrip("=")

    await message.reply(
        f"Here is your Link:\n"
        f"https://t.me/{temp.U_NAME}?start={encoded}"
    )


# ───────────────────────────────
# 🔹 BATCH FILE LINK
# ───────────────────────────────
@Client.on_message(filters.command(['batch', 'pbatch']) & filters.create(allowed))
async def gen_link_batch(bot, message):
    if " " not in message.text:
        return await message.reply(
            "Use correct format.\n"
            "Example <code>/batch https://t.me/VJ_Botz/10 https://t.me/VJ_Botz/20</code>"
        )

    cmd, first, last = message.text.split(" ", 2)

    regex = re.compile(
        r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?([\w\d_]+)/(\d+)$"
    )

    m1 = regex.match(first)
    m2 = regex.match(last)

    if not m1 or not m2:
        return await message.reply("Invalid Telegram message link.")

    f_chat_id = m1.group(4)
    l_chat_id = m2.group(4)

    f_msg_id = int(m1.group(5))
    l_msg_id = int(m2.group(5))

    if f_chat_id.isnumeric():
        f_chat_id = int("-100" + f_chat_id)
    if l_chat_id.isnumeric():
        l_chat_id = int("-100" + l_chat_id)

    if f_chat_id != l_chat_id:
        return await message.reply("Chat IDs do not match.")

    try:
        chat_id = (await bot.get_chat(f_chat_id)).id
    except ChannelInvalid:
        return await message.reply(
            "This may be a private channel.\n"
            "Make me admin to index files."
        )
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply("Invalid link.")
    except Exception as e:
        return await message.reply(f"Error: {e}")

    sts = await message.reply("Generating batch link, please wait...")

    # ───── FILE STORE CHANNEL (DSTORE)
    if chat_id in FILE_STORE_CHANNEL:
        data = f"{f_msg_id}_{l_msg_id}_{chat_id}_{cmd.lower().strip()}"
        encoded = base64.urlsafe_b64encode(
            data.encode("ascii")
        ).decode().rstrip("=")

        return await sts.edit(
            f"Here is your link:\n"
            f"https://t.me/{temp.U_NAME}?start=DSTORE-{encoded}"
        )

    # ───── NORMAL BATCH MODE
    files = []
    total = 0

    async for msg in bot.iter_messages(f_chat_id, l_msg_id, f_msg_id):
        if not msg.media or msg.empty or msg.service:
            continue

        media = getattr(msg, msg.media.value)
        caption = msg.caption.html if msg.caption else ""

        files.append({
            "file_id": media.file_id,
            "caption": caption,
            "title": getattr(media, "file_name", ""),
            "size": media.file_size,
            "protect": cmd.lower().strip() == "/pbatch"
        })

        total += 1

    if not files:
        return await sts.edit("No valid media found.")

    json_name = f"batchmode_{message.from_user.id}.json"

    with open(json_name, "w") as f:
        json.dump(files, f)

    post = await bot.send_document(
        LOG_CHANNEL,
        json_name,
        file_name="Batch.json",
        caption="⚠️ Generated for File Store"
    )

    os.remove(json_name)

    batch_file_id, _ = unpack_new_file_id(post.document.file_id)

    await sts.edit(
        f"Here is your link\n"
        f"Contains `{total}` files.\n"
        f"https://t.me/{temp.U_NAME}?start=BATCH-{batch_file_id}"
    )
