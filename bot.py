import logging
import os
import json
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)

ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
PRICES_FILE = os.path.join(DATA_DIR, "prices.json")
BANNED_FILE = os.path.join(DATA_DIR, "banned.json")

def load_json(file, default):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_prices():
    default = {
        "diamonds": {
            "86": "", "172": "", "257": "", "343": "", "429": "",
            "514": "", "600": "", "706": "", "878": "", "963": "",
            "1049": "", "1135": "", "1412": "", "1584": "", "1756": "",
            "2195": "", "2539": "", "2901": "", "3245": "", "3688": "",
            "4032": "", "4394": "", "4738": "", "5100": "", "5532": "",
            "6238": "", "7727": "", "9288": ""
        },
        "double": {"2x50": "", "2x150": "", "2x250": "", "2x500": ""},
        "weekly": {"weekly_pass": ""}
    }
    return load_json(PRICES_FILE, default)

def get_orders():
    return load_json(ORDERS_FILE, {})

def get_banned():
    return load_json(BANNED_FILE, [])

def next_order_id():
    orders = get_orders()
    if not orders:
        return "ORD001"
    nums = [int(k.replace("ORD", "")) for k in orders.keys() if k.startswith("ORD")]
    return f"ORD{(max(nums)+1):03d}" if nums else "ORD001"

def is_group(update: Update) -> bool:
    return update.effective_chat.type in ["group", "supergroup"]

def build_menu_text():
    prices = get_prices()
    text = "💎 *MLBB Diamond Top-up*\n"
    text += "━━━━━━━━━━━━━━━━━━━\n\n"
    text += "📌 *Diamond Packages*\n"
    for dia, price in prices["diamonds"].items():
        p = price if price else "—"
        text += f"  Dia {dia} — {p}\n"
    text += "\n📌 *2x Diamond*\n"
    for key, price in prices["double"].items():
        p = price if price else "—"
        text += f"  Dia {key} — {p}\n"
    text += "\n📌 *Weekly Pass*\n"
    wp = prices["weekly"].get("weekly_pass", "")
    text += f"  Weekly Pass — {wp if wp else '—'}\n"
    text += "\n━━━━━━━━━━━━━━━━━━━\n"
    text += "📦 *Order တင်နည်း:*\n"
    text += "`123456(1234)dia878`\n"
    text += "_(MLBB ID)(Server ID)(Package)_\n\n"
    text += "✅ Order တင်ပြီးနောက် bot ကို *private DM* မှာ screenshot ပို့ပါ။"
    return text

def parse_order(text):
    match = re.match(
        r"(\d+)\((\d+)\)(dia\d+(?:x\d+)?|2x\d+|weekly_pass|weekly pass)",
        text.strip(), re.IGNORECASE
    )
    if match:
        return {
            "mlbb_id": match.group(1),
            "server_id": match.group(2),
            "package": match.group(3).lower().replace(" ", "_")
        }
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in get_banned():
        await update.message.reply_text("🚫 သင့် account ကို ပိတ်ထားပါသည်။")
        return
    if is_group(update):
        await update.message.reply_text(build_menu_text(), parse_mode="Markdown")
    else:
        keyboard = [[InlineKeyboardButton("📋 Menu ကြည့်ရန်", callback_data="show_menu")]]
        await update.message.reply_text(
            "👋 *MLBB Top-up Bot မှ ကြိုဆိုပါသည်!*\n\nDiamond packages ကြည့်ရန် ခလုတ်နှိပ်ပါ။",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in get_banned():
        await update.message.reply_text("🚫 သင့် account ကို ပိတ်ထားပါသည်။")
        return
    await update.message.reply_text(build_menu_text(), parse_mode="Markdown")

async def show_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(build_menu_text(), parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    if not message or not message.text:
        return

    if user.id in get_banned():
        if not is_group(update):
            await message.reply_text("🚫 သင့် account ကို ပိတ်ထားပါသည်။")
        return

    text = message.text.strip()

    if is_group(update):
        parsed = parse_order(text)
        if not parsed:
            return
        order_id = next_order_id()
        orders = get_orders()
        orders[order_id] = {
            "order_id": order_id,
            "user_id": user.id,
            "username": user.username or user.first_name,
            "mlbb_id": parsed["mlbb_id"],
            "server_id": parsed["server_id"],
            "package": parsed["package"],
            "status": "pending_screenshot",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "screenshot": None
        }
        save_json(ORDERS_FILE, orders)
        bot_info = await context.bot.get_me()
        confirm_text = (
            f"✅ *Order လက်ခံပြီ!*\n\n"
            f"🆔 Order ID: `{order_id}`\n"
            f"🎮 MLBB ID: `{parsed['mlbb_id']}({parsed['server_id']})`\n"
            f"💎 Package: `{parsed['package']}`\n\n"
            f"📸 @{bot_info.username} ကို *private DM* ဖွင့်ပြီး\n"
            f"Order ID `{order_id}` ပို့ကာ screenshot ပေးပို့ပါ။"
        )
        keyboard = [[InlineKeyboardButton("🗑️ Delete Order", callback_data=f"user_delete_{order_id}")]]
        await message.reply_text(confirm_text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if context.user_data.get("awaiting_screenshot"):
        oid = context.user_data.get("pending_order_id", "")
        await message.reply_text(f"📸 Order `{oid}` အတွက် screenshot (photo) ပို့ပေးပါ။", parse_mode="Markdown")
        return

    oid_match = re.match(r"^(ORD\d+)$", text.upper())
    if oid_match:
        order_id = oid_match.group(1)
        orders = get_orders()
        if order_id in orders and orders[order_id]["user_id"] == user.id:
            o = orders[order_id]
            if o["status"] == "pending_screenshot":
                context.user_data["awaiting_screenshot"] = True
                context.user_data["pending_order_id"] = order_id
                await message.reply_text(
                    f"✅ Order `{order_id}` တွေ့ပြီ!\n💎 `{o['package']}` | 🎮 `{o['mlbb_id']}({o['server_id']})`\n\n📸 Payment screenshot (photo) ပို့ပေးပါ။",
                    parse_mode="Markdown"
                )
            elif o["status"] == "pending":
                await message.reply_text(f"⏳ `{order_id}` — Admin confirm စောင့်နေသည်။", parse_mode="Markdown")
            else:
                await message.reply_text(f"ℹ️ `{order_id}` — Status: {o['status']}", parse_mode="Markdown")
        else:
            await message.reply_text("⚠️ Order ID မတွေ့ပါ သို့မဟုတ် သင့် order မဟုတ်ပါ။")
        return

    await message.reply_text(
        "📦 Order တင်ရန် Group မှာ:\n`123456(1234)dia878`\nဟု ရိုက်ပါ။",
        parse_mode="Markdown"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if user.id in get_banned():
        return
    if is_group(update):
        return
    if not context.user_data.get("awaiting_screenshot"):
        await message.reply_text("⚠️ Order ID အရင်ပို့ပါ။ ဥပမာ: `ORD001`", parse_mode="Markdown")
        return

    order_id = context.user_data.get("pending_order_id")
    orders = get_orders()

    if not order_id or order_id not in orders:
        await message.reply_text("⚠️ Order မတွေ့ပါ။")
        return

    file_id = message.photo[-1].file_id
    orders[order_id]["screenshot"] = file_id
    orders[order_id]["status"] = "pending"
    save_json(ORDERS_FILE, orders)

    context.user_data["awaiting_screenshot"] = False
    context.user_data["pending_order_id"] = None

    o = orders[order_id]
    admin_keyboard = [
        [
            InlineKeyboardButton("✅ Complete", callback_data=f"complete_{order_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order_id}")
        ],
        [InlineKeyboardButton("🗑️ Delete", callback_data=f"admin_delete_{order_id}")]
    ]

    await context.bot.send_photo(
        chat_id=ADMIN_ID, photo=file_id,
        caption=(
            f"🆕 *New Order!*\n\n🆔 `{order_id}`\n"
            f"👤 @{o['username']} (`{o['user_id']}`)\n"
            f"🎮 `{o['mlbb_id']}({o['server_id']})`\n"
            f"💎 `{o['package']}`\n🕐 {o['timestamp']}"
        ),
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(admin_keyboard)
    )
    await message.reply_text(
        f"✅ *Screenshot လက်ခံပြီ!*\n🆔 `{order_id}`\n⏳ Admin confirm စောင့်ပါ။",
        parse_mode="Markdown"
    )

async def user_delete_order(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str):
    query = update.callback_query
    orders = get_orders()
    if order_id in orders and orders[order_id]["user_id"] == query.from_user.id:
        if orders[order_id]["status"] in ["pending_screenshot", "pending"]:
            del orders[order_id]
            save_json(ORDERS_FILE, orders)
            context.user_data["awaiting_screenshot"] = False
            context.user_data["pending_order_id"] = None
            await query.edit_message_text(f"🗑️ Order `{order_id}` ဖျက်ပြီး။", parse_mode="Markdown")
        else:
            await query.answer("⚠️ Processing ဖြစ်နေ၍ ဖျက်မရပါ။", show_alert=True)
    else:
        await query.answer("⚠️ သင့် order မဟုတ်ပါ။", show_alert=True)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "show_menu":
        await show_menu_callback(update, context)
        return
    if data.startswith("user_delete_"):
        await user_delete_order(update, context, data.replace("user_delete_", ""))
        return

    if query.from_user.id != ADMIN_ID:
        await query.answer("🚫 Admin only!", show_alert=True)
        return

    if data.startswith("complete_"):
        order_id = data.replace("complete_", "")
        orders = get_orders()
        if order_id in orders:
            orders[order_id]["status"] = "completed"
            save_json(ORDERS_FILE, orders)
            o = orders[order_id]
            await context.bot.send_message(
                chat_id=o["user_id"],
                text=f"✅ *Order Completed!*\n\n🆔 `{order_id}`\n💎 `{o['package']}`\n🎮 `{o['mlbb_id']}({o['server_id']})`\n\nDiamond ရောက်ပြီပါပြီ! ကျေးဇူးတင်ပါသည် 🙏",
                parse_mode="Markdown"
            )
            await query.edit_message_caption(caption=query.message.caption + "\n\n✅ *COMPLETED*", parse_mode="Markdown")

    elif data.startswith("reject_"):
        order_id = data.replace("reject_", "")
        orders = get_orders()
        if order_id in orders:
            orders[order_id]["status"] = "rejected"
            save_json(ORDERS_FILE, orders)
            o = orders[order_id]
            await context.bot.send_message(
                chat_id=o["user_id"],
                text=f"❌ *Order Rejected*\n\n🆔 `{order_id}`\n\nAdmin က reject လုပ်ပါသည်။ ပြဿနာရှိပါက admin ထံဆက်သွယ်ပါ။",
                parse_mode="Markdown"
            )
            await query.edit_message_caption(caption=query.message.caption + "\n\n❌ *REJECTED*", parse_mode="Markdown")

    elif data.startswith("admin_delete_"):
        order_id = data.replace("admin_delete_", "")
        orders = get_orders()
        if order_id in orders:
            del orders[order_id]
            save_json(ORDERS_FILE, orders)
            await query.edit_message_caption(caption=f"🗑️ `{order_id}` deleted.", parse_mode="Markdown")

async def admin_check(update: Update) -> bool:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admin only command!")
        return False
    return True

async def orders_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    orders = get_orders()
    if not orders:
        await update.message.reply_text("📭 Order မရှိသေးပါ။")
        return
    text = "📋 *Order List*\n━━━━━━━━━━━━━━━\n"
    icons = {"pending": "⏳", "completed": "✅", "rejected": "❌", "pending_screenshot": "📸"}
    for oid, o in list(orders.items())[-20:]:
        text += f"{icons.get(o['status'],'❓')} `{oid}` | @{o['username']} | {o['package']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage:\n`/setprice dia878 5000ks`\n`/setprice 2x50 2500ks`\n`/setprice weekly_pass 3000ks`", parse_mode="Markdown")
        return
    pkg = args[0].lower()
    price = " ".join(args[1:])
    prices = get_prices()
    pkg_key = pkg.replace("dia", "")
    updated = False
    if pkg_key in prices["diamonds"]:
        prices["diamonds"][pkg_key] = price; updated = True
    elif pkg in prices["double"]:
        prices["double"][pkg] = price; updated = True
    elif pkg in ["weekly_pass", "weekly"]:
        prices["weekly"]["weekly_pass"] = price; updated = True
    if updated:
        save_json(PRICES_FILE, prices)
        await update.message.reply_text(f"✅ `{pkg}` → `{price}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ `{pkg}` မတွေ့ပါ။", parse_mode="Markdown")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    if not context.args:
        await update.message.reply_text("Usage: `/ban <user_id>`", parse_mode="Markdown"); return
    try:
        uid = int(context.args[0])
        banned = get_banned()
        if uid not in banned:
            banned.append(uid); save_json(BANNED_FILE, banned)
            await update.message.reply_text(f"🚫 `{uid}` ban ပြုလုပ်ပြီး။", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ `{uid}` ban ခံပြီးဖြစ်သည်။", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("⚠️ User ID ဂဏန်းဖြင့်ထည့်ပါ။")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    if not context.args:
        await update.message.reply_text("Usage: `/unban <user_id>`", parse_mode="Markdown"); return
    try:
        uid = int(context.args[0])
        banned = get_banned()
        if uid in banned:
            banned.remove(uid); save_json(BANNED_FILE, banned)
            await update.message.reply_text(f"✅ `{uid}` unban ပြုလုပ်ပြီး။", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ `{uid}` ban မခံရပါ။", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("⚠️ User ID ဂဏန်းဖြင့်ထည့်ပါ။")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    if not context.args:
        await update.message.reply_text("Usage: `/broadcast <message>`", parse_mode="Markdown"); return
    msg = " ".join(context.args)
    orders = get_orders()
    sent_ids = set(); count = 0
    for o in orders.values():
        uid = o["user_id"]
        if uid not in sent_ids:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 *Admin:*\n{msg}", parse_mode="Markdown")
                sent_ids.add(uid); count += 1
            except: pass
    await update.message.reply_text(f"✅ {count} users ထံ ပို့ပြီး။")

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    await update.message.reply_text(
        "🛠️ *Admin Commands*\n━━━━━━━━━━━━━━━\n"
        "/orders — Order list\n/setprice dia878 5000ks\n"
        "/ban ID — ban\n/unban ID — unban\n"
        "/broadcast msg — all users\n/adminhelp — help",
        parse_mode="Markdown"
    )

def main():
    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0,
    )
    app = Application.builder().token(BOT_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("orders", orders_list))
    app.add_handler(CommandHandler("setprice", set_price))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("adminhelp", admin_help))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot started...")

    if WEBHOOK_URL:
        logger.info(f"Running with webhook: {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=7860,
            webhook_url=WEBHOOK_URL,
        )
    else:
        logger.info("Running with polling...")
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()import logging
import os
import json
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)

ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
PRICES_FILE = os.path.join(DATA_DIR, "prices.json")
BANNED_FILE = os.path.join(DATA_DIR, "banned.json")

def load_json(file, default):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_prices():
    default = {
        "diamonds": {
            "86": "", "172": "", "257": "", "343": "", "429": "",
            "514": "", "600": "", "706": "", "878": "", "963": "",
            "1049": "", "1135": "", "1412": "", "1584": "", "1756": "",
            "2195": "", "2539": "", "2901": "", "3245": "", "3688": "",
            "4032": "", "4394": "", "4738": "", "5100": "", "5532": "",
            "6238": "", "7727": "", "9288": ""
        },
        "double": {"2x50": "", "2x150": "", "2x250": "", "2x500": ""},
        "weekly": {"weekly_pass": ""}
    }
    return load_json(PRICES_FILE, default)

def get_orders():
    return load_json(ORDERS_FILE, {})

def get_banned():
    return load_json(BANNED_FILE, [])

def next_order_id():
    orders = get_orders()
    if not orders:
        return "ORD001"
    nums = [int(k.replace("ORD", "")) for k in orders.keys() if k.startswith("ORD")]
    return f"ORD{(max(nums)+1):03d}" if nums else "ORD001"

def is_group(update: Update) -> bool:
    return update.effective_chat.type in ["group", "supergroup"]

def build_menu_text():
    prices = get_prices()
    text = "💎 *MLBB Diamond Top-up*\n"
    text += "━━━━━━━━━━━━━━━━━━━\n\n"
    text += "📌 *Diamond Packages*\n"
    for dia, price in prices["diamonds"].items():
        p = price if price else "—"
        text += f"  Dia {dia} — {p}\n"
    text += "\n📌 *2x Diamond*\n"
    for key, price in prices["double"].items():
        p = price if price else "—"
        text += f"  Dia {key} — {p}\n"
    text += "\n📌 *Weekly Pass*\n"
    wp = prices["weekly"].get("weekly_pass", "")
    text += f"  Weekly Pass — {wp if wp else '—'}\n"
    text += "\n━━━━━━━━━━━━━━━━━━━\n"
    text += "📦 *Order တင်နည်း:*\n"
    text += "`123456(1234)dia878`\n"
    text += "_(MLBB ID)(Server ID)(Package)_\n\n"
    text += "✅ Order တင်ပြီးနောက် bot ကို *private DM* မှာ screenshot ပို့ပါ။"
    return text

def parse_order(text):
    match = re.match(
        r"(\d+)\((\d+)\)(dia\d+(?:x\d+)?|2x\d+|weekly_pass|weekly pass)",
        text.strip(), re.IGNORECASE
    )
    if match:
        return {
            "mlbb_id": match.group(1),
            "server_id": match.group(2),
            "package": match.group(3).lower().replace(" ", "_")
        }
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in get_banned():
        await update.message.reply_text("🚫 သင့် account ကို ပိတ်ထားပါသည်။")
        return
    if is_group(update):
        await update.message.reply_text(build_menu_text(), parse_mode="Markdown")
    else:
        keyboard = [[InlineKeyboardButton("📋 Menu ကြည့်ရန်", callback_data="show_menu")]]
        await update.message.reply_text(
            "👋 *MLBB Top-up Bot မှ ကြိုဆိုပါသည်!*\n\nDiamond packages ကြည့်ရန် ခလုတ်နှိပ်ပါ။",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in get_banned():
        await update.message.reply_text("🚫 သင့် account ကို ပိတ်ထားပါသည်။")
        return
    await update.message.reply_text(build_menu_text(), parse_mode="Markdown")

async def show_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(build_menu_text(), parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    if not message or not message.text:
        return

    if user.id in get_banned():
        if not is_group(update):
            await message.reply_text("🚫 သင့် account ကို ပိတ်ထားပါသည်။")
        return

    text = message.text.strip()

    if is_group(update):
        parsed = parse_order(text)
        if not parsed:
            return
        order_id = next_order_id()
        orders = get_orders()
        orders[order_id] = {
            "order_id": order_id,
            "user_id": user.id,
            "username": user.username or user.first_name,
            "mlbb_id": parsed["mlbb_id"],
            "server_id": parsed["server_id"],
            "package": parsed["package"],
            "status": "pending_screenshot",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "screenshot": None
        }
        save_json(ORDERS_FILE, orders)
        bot_info = await context.bot.get_me()
        confirm_text = (
            f"✅ *Order လက်ခံပြီ!*\n\n"
            f"🆔 Order ID: `{order_id}`\n"
            f"🎮 MLBB ID: `{parsed['mlbb_id']}({parsed['server_id']})`\n"
            f"💎 Package: `{parsed['package']}`\n\n"
            f"📸 @{bot_info.username} ကို *private DM* ဖွင့်ပြီး\n"
            f"Order ID `{order_id}` ပို့ကာ screenshot ပေးပို့ပါ။"
        )
        keyboard = [[InlineKeyboardButton("🗑️ Delete Order", callback_data=f"user_delete_{order_id}")]]
        await message.reply_text(confirm_text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if context.user_data.get("awaiting_screenshot"):
        oid = context.user_data.get("pending_order_id", "")
        await message.reply_text(f"📸 Order `{oid}` အတွက် screenshot (photo) ပို့ပေးပါ။", parse_mode="Markdown")
        return

    oid_match = re.match(r"^(ORD\d+)$", text.upper())
    if oid_match:
        order_id = oid_match.group(1)
        orders = get_orders()
        if order_id in orders and orders[order_id]["user_id"] == user.id:
            o = orders[order_id]
            if o["status"] == "pending_screenshot":
                context.user_data["awaiting_screenshot"] = True
                context.user_data["pending_order_id"] = order_id
                await message.reply_text(
                    f"✅ Order `{order_id}` တွေ့ပြီ!\n💎 `{o['package']}` | 🎮 `{o['mlbb_id']}({o['server_id']})`\n\n📸 Payment screenshot (photo) ပို့ပေးပါ။",
                    parse_mode="Markdown"
                )
            elif o["status"] == "pending":
                await message.reply_text(f"⏳ `{order_id}` — Admin confirm စောင့်နေသည်။", parse_mode="Markdown")
            else:
                await message.reply_text(f"ℹ️ `{order_id}` — Status: {o['status']}", parse_mode="Markdown")
        else:
            await message.reply_text("⚠️ Order ID မတွေ့ပါ သို့မဟုတ် သင့် order မဟုတ်ပါ။")
        return

    await message.reply_text(
        "📦 Order တင်ရန် Group မှာ:\n`123456(1234)dia878`\nဟု ရိုက်ပါ။",
        parse_mode="Markdown"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if user.id in get_banned():
        return
    if is_group(update):
        return
    if not context.user_data.get("awaiting_screenshot"):
        await message.reply_text("⚠️ Order ID အရင်ပို့ပါ။ ဥပမာ: `ORD001`", parse_mode="Markdown")
        return

    order_id = context.user_data.get("pending_order_id")
    orders = get_orders()

    if not order_id or order_id not in orders:
        await message.reply_text("⚠️ Order မတွေ့ပါ။")
        return

    file_id = message.photo[-1].file_id
    orders[order_id]["screenshot"] = file_id
    orders[order_id]["status"] = "pending"
    save_json(ORDERS_FILE, orders)

    context.user_data["awaiting_screenshot"] = False
    context.user_data["pending_order_id"] = None

    o = orders[order_id]
    admin_keyboard = [
        [
            InlineKeyboardButton("✅ Complete", callback_data=f"complete_{order_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order_id}")
        ],
        [InlineKeyboardButton("🗑️ Delete", callback_data=f"admin_delete_{order_id}")]
    ]

    await context.bot.send_photo(
        chat_id=ADMIN_ID, photo=file_id,
        caption=(
            f"🆕 *New Order!*\n\n🆔 `{order_id}`\n"
            f"👤 @{o['username']} (`{o['user_id']}`)\n"
            f"🎮 `{o['mlbb_id']}({o['server_id']})`\n"
            f"💎 `{o['package']}`\n🕐 {o['timestamp']}"
        ),
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(admin_keyboard)
    )
    await message.reply_text(
        f"✅ *Screenshot လက်ခံပြီ!*\n🆔 `{order_id}`\n⏳ Admin confirm စောင့်ပါ။",
        parse_mode="Markdown"
    )

async def user_delete_order(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str):
    query = update.callback_query
    orders = get_orders()
    if order_id in orders and orders[order_id]["user_id"] == query.from_user.id:
        if orders[order_id]["status"] in ["pending_screenshot", "pending"]:
            del orders[order_id]
            save_json(ORDERS_FILE, orders)
            context.user_data["awaiting_screenshot"] = False
            context.user_data["pending_order_id"] = None
            await query.edit_message_text(f"🗑️ Order `{order_id}` ဖျက်ပြီး။", parse_mode="Markdown")
        else:
            await query.answer("⚠️ Processing ဖြစ်နေ၍ ဖျက်မရပါ။", show_alert=True)
    else:
        await query.answer("⚠️ သင့် order မဟုတ်ပါ။", show_alert=True)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "show_menu":
        await show_menu_callback(update, context)
        return
    if data.startswith("user_delete_"):
        await user_delete_order(update, context, data.replace("user_delete_", ""))
        return

    if query.from_user.id != ADMIN_ID:
        await query.answer("🚫 Admin only!", show_alert=True)
        return

    if data.startswith("complete_"):
        order_id = data.replace("complete_", "")
        orders = get_orders()
        if order_id in orders:
            orders[order_id]["status"] = "completed"
            save_json(ORDERS_FILE, orders)
            o = orders[order_id]
            await context.bot.send_message(
                chat_id=o["user_id"],
                text=f"✅ *Order Completed!*\n\n🆔 `{order_id}`\n💎 `{o['package']}`\n🎮 `{o['mlbb_id']}({o['server_id']})`\n\nDiamond ရောက်ပြီပါပြီ! ကျေးဇူးတင်ပါသည် 🙏",
                parse_mode="Markdown"
            )
            await query.edit_message_caption(caption=query.message.caption + "\n\n✅ *COMPLETED*", parse_mode="Markdown")

    elif data.startswith("reject_"):
        order_id = data.replace("reject_", "")
        orders = get_orders()
        if order_id in orders:
            orders[order_id]["status"] = "rejected"
            save_json(ORDERS_FILE, orders)
            o = orders[order_id]
            await context.bot.send_message(
                chat_id=o["user_id"],
                text=f"❌ *Order Rejected*\n\n🆔 `{order_id}`\n\nAdmin က reject လုပ်ပါသည်။ ပြဿနာရှိပါက admin ထံဆက်သွယ်ပါ။",
                parse_mode="Markdown"
            )
            await query.edit_message_caption(caption=query.message.caption + "\n\n❌ *REJECTED*", parse_mode="Markdown")

    elif data.startswith("admin_delete_"):
        order_id = data.replace("admin_delete_", "")
        orders = get_orders()
        if order_id in orders:
            del orders[order_id]
            save_json(ORDERS_FILE, orders)
            await query.edit_message_caption(caption=f"🗑️ `{order_id}` deleted.", parse_mode="Markdown")

async def admin_check(update: Update) -> bool:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admin only command!")
        return False
    return True

async def orders_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    orders = get_orders()
    if not orders:
        await update.message.reply_text("📭 Order မရှိသေးပါ။")
        return
    text = "📋 *Order List*\n━━━━━━━━━━━━━━━\n"
    icons = {"pending": "⏳", "completed": "✅", "rejected": "❌", "pending_screenshot": "📸"}
    for oid, o in list(orders.items())[-20:]:
        text += f"{icons.get(o['status'],'❓')} `{oid}` | @{o['username']} | {o['package']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage:\n`/setprice dia878 5000ks`\n`/setprice 2x50 2500ks`\n`/setprice weekly_pass 3000ks`", parse_mode="Markdown")
        return
    pkg = args[0].lower()
    price = " ".join(args[1:])
    prices = get_prices()
    pkg_key = pkg.replace("dia", "")
    updated = False
    if pkg_key in prices["diamonds"]:
        prices["diamonds"][pkg_key] = price; updated = True
    elif pkg in prices["double"]:
        prices["double"][pkg] = price; updated = True
    elif pkg in ["weekly_pass", "weekly"]:
        prices["weekly"]["weekly_pass"] = price; updated = True
    if updated:
        save_json(PRICES_FILE, prices)
        await update.message.reply_text(f"✅ `{pkg}` → `{price}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ `{pkg}` မတွေ့ပါ။", parse_mode="Markdown")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    if not context.args:
        await update.message.reply_text("Usage: `/ban <user_id>`", parse_mode="Markdown"); return
    try:
        uid = int(context.args[0])
        banned = get_banned()
        if uid not in banned:
            banned.append(uid); save_json(BANNED_FILE, banned)
            await update.message.reply_text(f"🚫 `{uid}` ban ပြုလုပ်ပြီး။", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ `{uid}` ban ခံပြီးဖြစ်သည်။", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("⚠️ User ID ဂဏန်းဖြင့်ထည့်ပါ။")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    if not context.args:
        await update.message.reply_text("Usage: `/unban <user_id>`", parse_mode="Markdown"); return
    try:
        uid = int(context.args[0])
        banned = get_banned()
        if uid in banned:
            banned.remove(uid); save_json(BANNED_FILE, banned)
            await update.message.reply_text(f"✅ `{uid}` unban ပြုလုပ်ပြီး။", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ `{uid}` ban မခံရပါ။", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("⚠️ User ID ဂဏန်းဖြင့်ထည့်ပါ။")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    if not context.args:
        await update.message.reply_text("Usage: `/broadcast <message>`", parse_mode="Markdown"); return
    msg = " ".join(context.args)
    orders = get_orders()
    sent_ids = set(); count = 0
    for o in orders.values():
        uid = o["user_id"]
        if uid not in sent_ids:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 *Admin:*\n{msg}", parse_mode="Markdown")
                sent_ids.add(uid); count += 1
            except: pass
    await update.message.reply_text(f"✅ {count} users ထံ ပို့ပြီး။")

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update): return
    await update.message.reply_text(
        "🛠️ *Admin Commands*\n━━━━━━━━━━━━━━━\n"
        "/orders — Order list\n/setprice dia878 5000ks\n"
        "/ban ID — ban\n/unban ID — unban\n"
        "/broadcast msg — all users\n/adminhelp — help",
        parse_mode="Markdown"
    )

def main():
    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0,
    )
    app = Application.builder().token(BOT_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("orders", orders_list))
    app.add_handler(CommandHandler("setprice", set_price))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("adminhelp", admin_help))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot started...")

    if WEBHOOK_URL:
        logger.info(f"Running with webhook: {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=7860,
            webhook_url=WEBHOOK_URL,
        )
    else:
        logger.info("Running with polling...")
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
