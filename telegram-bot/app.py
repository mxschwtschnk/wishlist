import os, secrets, uuid
"This is a public wishlist bot.\n\n"
"*Creator* → /newlist <name>, /invite, /addurl <url> (in Mini App), /mylist, /received <id>, /dontwant <id>\n"
"*Guest* → /join <code>, /view, /reserve <id>, /unreserve <id>\n\n"
"Use /app to open the Mini App UI."
)
await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def app_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not WEBAPP_URL:
await update.message.reply_text("Mini App URL is not configured.")
return
kb = [[KeyboardButton(text="Open app", web_app=WebAppInfo(url=WEBAPP_URL))]]
await update.message.reply_text("Open the mini app:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))


async def newlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
args = (update.message.text or '').split(' ', 1)
if len(args) < 2 or not args[1].strip():
await update.message.reply_text("Usage: /newlist <name>")
return
name = args[1].strip()
with Session(engine) as s:
if not s.get(User, update.effective_user.id): s.add(User(tg_id=update.effective_user.id)); s.commit()
wl = Wishlist(owner_tg_id=update.effective_user.id, name=name)
s.add(wl); s.commit()
await update.message.reply_text(f"✅ List *{name}* created. Use /invite to add guests.", parse_mode=ParseMode.MARKDOWN)


async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
with Session(engine) as s:
wl = s.query(Wishlist).filter(Wishlist.owner_tg_id==update.effective_user.id).order_by(Wishlist.id.desc()).first()
if not wl:
await update.message.reply_text("Create a list first: /newlist <name>")
return
if not wl.invite_code:
wl.invite_code = secrets.token_urlsafe(6); s.commit()
await update.message.reply_text(f"Invite code: `{wl.invite_code}`\nGuests: /join <code>", parse_mode=ParseMode.MARKDOWN)


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
args = (update.message.text or '').split(' ', 1)
if len(args) < 2:
await update.message.reply_text("Usage: /join <code>")
return
code = args[1].strip()
with Session(engine) as s:
wl = s.query(Wishlist).filter(Wishlist.invite_code==code).first()
if not wl:
await update.message.reply_text("Code not found.")
return
if not s.get(User, update.effective_user.id): s.add(User(tg_id=update.effective_user.id)); s.commit()
if not s.query(Membership).filter(Membership.wishlist_id==wl.id, Membership.tg_user_id==update.effective_user.id).first():
s.add(Membership(wishlist_id=wl.id, tg_user_id=update.effective_user.id, role='guest'))
ga = s.get(GuestActive, update.effective_user.id)
if not ga: s.add(GuestActive(tg_user_id=update.effective_user.id, wishlist_id=wl.id))
else: ga.wishlist_id = wl.id; ga.updated_at = datetime.now(timezone.utc)
s.commit()
await update.message.reply_text("Joined! Open /view or use /app to open the Mini App.")


# (Опционально) текстовые команды для просмотра/резерва через чат
# можно добавить позже, так как Mini App закрывает основной сценарий


async def on_startup(app):
if WEBHOOK_BASE_URL:
await app.bot.set_webhook(url=f"{WEBHOOK_BASE_URL}/webhook/{app.bot.id}")


def main():
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("app", app_cmd))
app.add_handler(CommandHandler("newlist", newlist))
app.add_handler(CommandHandler("invite", invite))
app.add_handler(CommandHandler("join", join))
app.post_init = on_startup
app.run_webhook(listen="0.0.0.0", port=PORT, webhook_url=None)


if __name__ == "__main__":
from telegram.ext import CommandHandler
main()
