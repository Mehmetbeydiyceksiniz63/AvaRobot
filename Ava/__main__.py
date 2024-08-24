# <============================================== IMPORTS =========================================================>
import importlib
import re
import time
import asyncio
from platform import python_version as y
from sys import argv
from pyrogram import __version__ as pyrover
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram import __version__ as telever
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop
from telegram.utils.helpers import escape_markdown
from telethon import __version__ as tlhver

import JarvisRobo.modules.no_sql.users_db as sql
from JarvisRobo import (
    BOT_NAME,
    BOT_USERNAME,
    LOGGER,
    OWNER_ID,
    START_IMG,
    HELP_IMG,
    SUPPORT_CHAT,
    TOKEN,
    StartTime,
    dispatcher,
    pbot,
    telethn,
    updater,
)
from JarvisRobo.modules import ALL_MODULES
from JarvisRobo.modules.helper_funcs.chat_status import is_user_admin
from JarvisRobo.modules.helper_funcs.misc import paginate_modules

# <=======================================================================================================>

# <============================================== FUNCTIONS =========================================================>

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

# <============================================== STRINGS =========================================================>

PM_START_TEX = """
merhaba`{}`, nasılsın \n . . . 
"""


PM_START_TEXT = """ 
*merhaba* {}  

*๏ ben* {} !
➻ grubunuzda size yardım etmek için tasarlandım.
─────────────────
   *➻ kullanıcı»* {}
   *➻ grup »* {}
─────────────────
*๏ yardım almak için yardım komutuna tıkla.*
"""

buttons = [
   [
        InlineKeyboardButton(
            text="beni grubuna ekle",
            url=f"https://t.me/{dispatcher.bot.username}?startgroup=true",
        ),
    ],
   [
        InlineKeyboardButton(text="yardım & komutlar", callback_data="help_back"),
    ],
    [
        InlineKeyboardButton(text="❄ hakkımda ❄", callback_data="Jarvis_"),
        InlineKeyboardButton(text="✨ destek grubu ✨", url=f"https://t.me/kumsalmuzikk"),
    ],
   [
        InlineKeyboardButton(text="🥀 sahibi 🥀", url=f"tg://user?id={OWNER_ID}"),
        InlineKeyboardButton(text="☁️ kaynak kod ☁️", callback_data="source_"),
    ],
]

HELP_STRINGS = f"""
» {BOT_NAME}  tıklamak.  Belirli komut hakkında açıklama almak için aşağıdaki düğme"""

# <============================================== STRINGS END =========================================================>

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("JarvisRobo.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module



# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_photo(
        chat_id=chat_id,
        photo=START_IMG,
        caption=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )
# <============================================== START =========================================================>

def start(update: Update, context: CallbackContext):
    args = context.args
    global uptime
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="๏ geri ๏", callback_data="help_back")]]
                    ),
                )
            elif args[0].lower() == "markdownhelp":
                IMPORTED["exᴛʀᴀs"].markdown_help_sender(update)
            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rᴜʟᴇs" in IMPORTED:
                IMPORTED["rᴜʟᴇs"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            update.effective_message.reply_sticker(
                "CAACAgEAAx0Cfbdm0QACATNmC-1-nl8Unb8cLRS-8qfLllewvwACPwMAAtKbsEQsyzfIkYLVGx4E"
            )
            usr = update.effective_user
            lol = update.effective_message.reply_text(
                PM_START_TEX.format(usr.first_name), parse_mode=ParseMode.MARKDOWN
            )
            time.sleep(1.25)
            lol.edit_text("💻")
            time.sleep(1.0)
            lol.edit_text("bot başlatılıyor... ")
            time.sleep(0.5)
            lol.delete()
            
            update.effective_message.reply_photo(START_IMG, PM_START_TEXT.format(escape_markdown(first_name), BOT_NAME, sql.num_users(), sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_photo(
            START_IMG,
            caption="aktifim bebeğim  !\n<b>dun geceden biri. Hiç. Uyumadım :</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
        )

# <============================================== START END =========================================================>

def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors

# <============================================== HELP =========================================================>

def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "» *yardım komutlarım* *{}* :\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_caption(text,
                parse_mode=ParseMode.MARKDOWN,
                
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(text="geri", callback_data="help_back")]
                    ]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_caption(HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_caption(HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_caption(HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass
# <============================================== HELP CLOSE =========================================================>

# <============================================== ABOUT CALLBACK =========================================================>

def Jarvis_about_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "Jarvis_":
        uptime = get_readable_time((time.time() - StartTime))
        query.message.edit_caption(
            f"merhaba,*🥀\n  *ben {dispatcher.bot.first_name}"
            "\n Grubunuzu kolayca yönetmenize ve grubunuzu dolandırıcılardan ve spam gönderenlerden korumanıza yardımcı olmak için oluşturulmuş güçlü grup yönetimi."
            "\veritabanı olarak sqlalchemy ve mongodb ile python ile yazılmıştır."
            "\n\n────────────────────"
            f"\n*➻ zaman»* {uptime}"
            f"\n*➻ kullanıcı »* {sql.num_users()}"
            f"\n*➻ chat sayısı »* {sql.num_chats()}"
            "\n────────────────────"
            "\n\n➲  kullanıcıları kısıtlayabilirim."
            "\n➲   Gelişmiş bir su baskını önleme sistemine sahip olun."
            "\n➲  güvendiğiniz bir robotunuz olsun."
            "\n➲  etiket atabilirim oyun indirirm şarkıindiririm."
            "\n➲  üyeleri. karşilaya bilirim sohbet ederim ."
            f"\n\n➻ ve dahasını yababilirim benim adım {dispatcher.bot.first_name}.",
            parse_mode=ParseMode.MARKDOWN,
            
             reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="🎧destek grubu🎧", callback_data="kumsalmuzikk"),
                        InlineKeyboardButton(text="🌹sahibi🌹", url=f"tg://user?id={OWNER_ID}"),
                    ],
                    [
                        
                        InlineKeyboardButton(text="üst menü", callback_data="help_back"),
                    ],
                    [
                        InlineKeyboardButton(text="๏ geri๏", callback_data="Jarvis_back"),
                    ],
                ]
            ),
        ) 
    elif query.data == "Jarvis_support":
        query.message.edit_caption("๏ Yardım ve daha fazla bilgi almak için aşağıda verilen düğmelere tıklayın"
            f"\n\n formatlar {dispatcher.bot.first_name} yotube {dispatcher.bot.first_name}, yanılgı.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="🍷destek grubu🍷", url=f"https://t.me/{SUPPORT_CHAT}"
                        ),
                        InlineKeyboardButton(
                            text="🍷destek Kanalı🍷", url=f"https://t.me/kumsaldestekkanal"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="🌹SAHİBİ🌹", url=f"tg://user?id={OWNER_ID}"
                        ),
                        InlineKeyboardButton(
                            text="✅kaynak kod✅", url="https://github.com/doraemon890",
                        ),
                    ],
                    [
                        InlineKeyboardButton(text="๏ geri ๏", callback_data="Jarvis_"),
                    ],
                ]
            ),
        )
    elif query.data == "Jarvis_back":
        first_name = update.effective_user.first_name 
        query.message.edit_caption(
            PM_START_TEXT.format(escape_markdown(first_name), BOT_NAME,sql.num_users(),sql.num_chats()),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60,
        )
        
# <============================================== ABOUT CALLBACK END =========================================================>

# <============================================== SOURCE CALLBACK =========================================================>

def Source_about_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "source_":
        query.message.edit_caption(
            f"""
Merhaba,
 ben {BOT_NAME},

benim yardımımla grubu yönetici 


Python'un yardımıyla yazılmıştır : [telehon ekibi](https://github.com/LonamiWebs/Telethon)
[pyogram](https://github.com/pyrogram/pyrogram)
[payce ve repo ekibi](https://github.com/python-telegram-bot/python-telegram-bot)
Lisanslar [sǫʟᴀʟᴄʜᴇᴍʏ](https://www.sqlalchemy.org) ve [ᴍᴏɴɢᴏ](https://cloud.mongodb.com) son olarak database.


Kaynak koduna tıkla : [buraya tıkla](https://github.com/doraemon890/JARVIS-X-ROBO)


{BOT_NAME} kapsamında lisanslanmıştı :  [mit lisansı](https://github.com/doraemon890/JARVIS-X-ROBO/master/LICENSE).
© 2024 - 2025 | [destek grubu](https://t.me/{SUPPORT_CHAT}), destek grubundan yardım alabilirsiniz.
""",
            parse_mode=ParseMode.MARKDOWN,
            
            reply_markup=InlineKeyboardMarkup(
                [
             [
                 InlineKeyboardButton(text="✅kaynak Kod✅", url="https://github.com/doraemon890/JARVIS-X-ROBO")
             ],
                 [InlineKeyboardButton(text="๏ geri ๏", callback_data="source_back")]
                ]
            ),
        )
    elif query.data == "source_back":
        first_name = update.effective_user.first_name
        query.message.edit_caption(
            PM_START_TEXT.format(escape_markdown(first_name), BOT_NAME,sql.num_users(),sql.num_chats()),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60,
            
        )
# <============================================== SOURCE CALLBACK END =========================================================>

# <============================================== HELP MENU  =========================================================>

def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_photo(HELP_IMG,
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text=" yardım ",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_photo(HELP_IMG,"» Ayarlar menüsünü nerede açmak istiyorsunuz?.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="🌹grup ayarlarını aç🌹",
                            url="https://t.me/{}?start=help".format(context.bot.username),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="👥 üst menü👥",
                            callback_data="help_back",
                        )
                    ],
                ]
            ),
        )
        return

    elif l