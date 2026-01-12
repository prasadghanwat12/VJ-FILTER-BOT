# Don't Remove Credit @VJ_Botz
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


# ───────────────────────── SINGLE LINK ───────────────────────── #

@Client.on_message(filters.command(['link', 'plink']) & filters.create(allowed))
async def gen_link_s(bot, message):
    vj = await bot.ask(
        chat_id=message.from_user.id,
        text="Now Send Me Your Message Which You Want To Store."
    )

    file_type = vj.media
    if file_type not in [
        enums.MessageMediaType.VIDEO,
        enums.MessageMediaType.AUDIO,
        enums.MessageMediaType.DOCUMENT
    ]:
        return await vj.reply("Send me only video, audio or document.")

    if message.has_protected_content and message.chat.id not in ADMINS:
        return await message.reply("okDa")

    # ✅ FIXED HERE
    file_id, ref, *_ = unpack_new_file_id(
        (getattr(vj, file_type.value)).file_id
    )

    string = 'filep_' if message.text.lower().strip() == "/plink" else 'file_'
    string += file_id
    outstr = base64.urlsafe_b64encode(
        string.encode("ascii")
    ).decode().strip("=")

    await message.reply(
        f"Here is your Link:\nhttps://t.me/{temp.U_NAME}?start={outstr}"
    )


# ───────────────────────── BATCH LINK ───────────────────────── #

@Client.on_message(filters.command(['batch', 'pbatch']) & filters.create(allowed))
async def gen_link_batch(bot, message):

    if " " not in message.text:
        return await message.reply(
            "Use correct format.\n"
            "Example <code>/batch https://t.me/VJ_Botz/10 https://t.me/VJ_Botz/20</code>."
        )

    links = message.text.strip().split(" ")
    if len(links) != 3:
        return await message.reply(
            "Use correct format.\n"
            "Example <code>/batch https://t.me/VJ_Botz/10 https://t.me/VJ_Botz/20</code>."
        )

    cmd, first, last = links
    regex = re.compile(
        "(https://)?(t\\.me/|telegram\\.me/|telegram\\.dog/)"
        "(c/)?(\\d+|[a-zA-Z_0-9]+)/([0-9]+)$"
    )

    match = regex.match(first)
    if not match:
        return await message.reply('Invalid link')

    f_chat_id = match.group(4)
    f_msg_id = int(match.group(5))
    if f_chat_id.isnumeric():
        f_chat_id = int("-100" + f_chat_id)

    match = regex.match(last)
    if not match:
        return await message.reply('Invalid link')

    l_chat_id = match.group(4)
    l_msg_id = int(match.group(5))
    if l_chat_id.isnumeric():
        l_chat_id = int("-100" + l_chat_id)

    if f_chat_id != l_chat_id:
        return await message.reply("Chat ids not matched.")

    try:
        chat_id = (await bot.get_chat(f_chat_id)).id
    except ChannelInvalid:
        return await message.reply(
            'This may be a private channel / group. '
            'Make me an admin over there to index the files.'
        )
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        return await message.reply(f'Errors - {e}')

    sts = await message.reply(
        "Generating link for your message.\n"
        "This may take time depending upon number of messages"
    )

    if chat_id in FILE_STORE_CHANNEL:
        string = f"{f_msg_id}_{l_msg_id}_{chat_id}_{cmd.lower().strip()}"
        b_64 = base64.urlsafe_b64encode(
            string.encode("ascii")
        ).decode().strip("=")

        return await sts.edit(
            f"Here is your link\n"
            f"https://t.me/{temp.U_NAME}?start=DSTORE-{b_64}"
        )

    outlist = []
    og_msg = 0

    async for msg in bot.iter_messages(f_chat_id, l_msg_id, f_msg_id):
        if msg.empty or msg.service or not msg.media:
            continue

        try:
            file_type = msg.media
            file = getattr(msg, file_type.value)
            caption = msg.caption.html if msg.caption else ""

            if file:
                outlist.append({
                    "file_id": file.file_id,
                    "caption": caption,
                    "title": getattr(file, "file_name", ""),
                    "size": file.file_size,
                    "protect": cmd.lower().strip() == "/pbatch",
                })
                og_msg += 1
        except:
            pass

    json_name = f"batchmode_{message.from_user.id}.json"
    with open(json_name, "w+") as out:
        json.dump(outlist, out)

    post = await bot.send_document(
        LOG_CHANNEL,
        json_name,
        file_name="Batch.json",
        caption="⚠️Generated for filestore."
    )

    os.remove(json_name)

    # ✅ FIXED HERE
    file_id, ref, *_ = unpack_new_file_id(post.document.file_id)

    await sts.edit(
        f"Here is your link\n"
        f"Contains `{og_msg}` files.\n"
        f"https://t.me/{temp.U_NAME}?start=BATCH-{file_id}"
    )
