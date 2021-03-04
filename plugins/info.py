""" To check User's Info, Is Banned or Not """

# By @Krishna_Singhal

import json
from datetime import datetime

import aiohttp
import spamwatch

from userge import userge, Config, Message, get_collection

GBAN_USER_BASE = get_collection("GBAN_USER")
GMUTE_USER_BASE = get_collection("GMUTE_USER")


@userge.on_cmd("info", about={
    'header': "To check User's info",
    'usage': "{tr}info [for own info]\n"
             "{tr}info [Username | User Id]\n"
             "{tr}info [reply to User]"}, allow_via_bot=False)
async def info(msg: Message):
    """ To check User's info """
    await msg.edit("`Sedang menyelidiki pengguna...`")
    user_id = msg.input_str
    replied = msg.reply_to_message
    if not user_id:
        if replied:
            user_id = replied.forward_from.id if replied.forward_from else replied.from_user.id
        else:
            user_id = msg.from_user.id
    try:
        user = await msg.client.get_users(user_id)
    except Exception:
        await msg.edit("Pengguna tidak dikenal...")
        return
    await msg.edit("__Mendapat informasi dari database telegram...__")
    l_name = user.last_name or ''
    if user.username:
        username = '@' + user.username
    else:
        username = '`None`'
    common_chats = await msg.client.get_common_chats(user.id)
    user_info = f"""
**About [{user.first_name} {l_name}](tg://user?id={user.id})**:
  - **ID Pengguna**: `{user.id}`
  - **Pusat Data Ke**: `{user.dc_id}`
  - **Tag Pengguna**: {username}
  - **Terakhir Hidup**: `{last_online(user)}`
  - **Total Grub**: `{len(common_chats)}`
  - **Kontak*: `{user.is_contact}`
        """
    if user:
        if Config.SPAM_WATCH_API:
            status = spamwatch.Client(Config.SPAM_WATCH_API).get_ban(user.id)
            if status is False:
                user_info += "\n**Diblokir SpamWatch** : `❎`\n"
            else:
                user_info += "\n**Diblokir SpamWatch** : `✅`\n"
                user_info += f"    **● Alasan** : `{status.reason or None}`\n"
                user_info += f"    **● Pesan** : `{status.message or None}`\n"
        else:
            user_info += "\n**SpamWatch** : `Untuk mendapatkan informasinya, save var`\n"

        async with aiohttp.ClientSession() as ses:
            async with ses.get(
                f"https://api.intellivoid.net/spamprotection/v1/lookup?query={user_id}"
            ) as i_v:
                iv = json.loads(await i_v.text())
            async with ses.get(f'https://api.cas.chat/check?user_id={user.id}') as c_s:
                cas_banned = json.loads(await c_s.text())
        user_gbanned = await GBAN_USER_BASE.find_one({'user_id': user.id})
        user_gmuted = await GMUTE_USER_BASE.find_one({'user_id': user.id})

        if iv['success'] and iv['results']['attributes']['is_blacklisted'] is True:
            reason = iv['results']['attributes']['blacklist_reason']
            user_info += "**Perlindungan Spam Intellivoid** : `✅`\n"
            user_info += f"    **● Alasan** : `{reason}`\n"
        else:
            user_info += "**Perlindungan Spam Intellivoid** : `❎`\n"
        if cas_banned['ok']:
            reason = cas_banned['result']['messages'][0] or None
            user_info += "**Diblokir Antispam** : `✅`\n"
            user_info += f"    **● Alasan** : `{reason}`\n"
        else:
            user_info += "**Diblokir AntiSpam** : `❎`\n"
        if user_gmuted:
            user_info += "**Status GMuted** : `✅`\n"
            user_info += f"    **● Alasan** : `{user_gmuted['reason'] or None}`\n"
        else:
            user_info += "**Status GMuted** : `❎`\n"
        if user_gbanned:
            user_info += "**Status GBanned** : `✅`\n"
            user_info += f"    **● Alasan** : `{user_gbanned['reason'] or None}`"
        else:
            user_info += "**Status Gbanned** : `❎`"
        await msg.edit_or_send_as_file(text=user_info, disable_web_page_preview=True)


def last_online(user):
    time = ""
    if user.is_bot:
        time += "🤖 Dia Bot :("
    elif user.status == 'recently':
        time += "Baru saja"
    elif user.status == 'within_week':
        time += "Dalam seminggu terakhir"
    elif user.status == 'within_month':
        time += "Dalam sebulan terakhir"
    elif user.status == 'long_time_ago':
        time += "Sudah Meninggal :("
    elif user.status == 'online':
        time += "Sedang bernafas"
    elif user.status == 'offline':
        time += datetime.fromtimestamp(user.last_online_date).strftime("%a, %d %b %Y, %H:%M:%S")
    return time
