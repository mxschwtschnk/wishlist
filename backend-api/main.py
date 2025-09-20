import os, hmac, hashlib, time, re, uuid


def fmt_price(cents: Optional[int], cur: Optional[str]) -> str:
if cents is None: return ""
val = f"{cents/100:,.2f}".replace(",", " ").replace(".", ",")
sym = SYM.get((cur or '').upper(), cur or '')
return f"{val} {sym}".strip()


# --- API models ---
class AddUrlIn(BaseModel): url: str
class BotIdIn(BaseModel): bot_id: str


# --- Mini App endpoints ---
@app.get("/api/view")
def api_view(x_telegram_init: str = Header(None, convert_underscores=True)):
if not x_telegram_init: raise HTTPException(401, "Missing init data")
data = verify_init_data(x_telegram_init)
tg_user = int(eval(data.get('user', '{}')).get('id')) if 'user' in data else int(data.get('tg_user_id','0') or 0)
if not tg_user: raise HTTPException(401, "No user")
with Session(engine) as s:
# ensure user
if not s.get(User, tg_user): s.add(User(tg_id=tg_user)); s.commit()
# find active wishlist (guest) or last owned (owner)
ga = s.get(GuestActive, tg_user)
wl = s.get(Wishlist, ga.wishlist_id) if ga else s.query(Wishlist).filter(Wishlist.owner_tg_id==tg_user).order_by(Wishlist.id.desc()).first()
if not wl: return {"is_owner": False, "items": []}
is_owner = (wl.owner_tg_id == tg_user)
items = s.query(Item).filter(Item.wishlist_id==wl.id).all()
res_map = { r.bot_id: r for r in s.query(Reservation).filter(Reservation.wishlist_id==wl.id).all() }
out=[]
for it in items:
r = res_map.get(it.bot_id)
status = r.status if r else 'available'
if not is_owner:
if status in ('hidden','received'): continue
if status=='reserved' and r.user_tg_id!=tg_user: continue
out.append({
"bot_id": it.bot_id,
"title": it.title,
"url": it.url,
"price_cents": it.price_cents,
"currency": it.currency,
"image_url": it.image_url,
"mine": (status=='reserved' and r and r.user_tg_id==tg_user)
})
return {"is_owner": is_owner, "items": out}


@app.post("/api/addurl")
def api_addurl(inp: AddUrlIn, x_telegram_init: str = Header(None, convert_underscores=True)):
data = verify_init_data(x_telegram_init or "")
tg_user = int(eval(data.get('user', '{}')).get('id')) if 'user' in data else int(data.get('tg_user_id','0') or 0)
with Session(engine) as s:
wl = s.query(Wishlist).filter(Wishlist.owner_tg_id==tg_user).order_by(Wishlist.id.desc()).first()
if not wl: raise HTTPException(400, "No list. Create one in the bot.")
info = parse_product(inp.url)
bot_id = str(uuid.uuid4())[:8]
s.add(Item(wishlist_id=wl.id, bot_id=bot_id, title=info['title'], url=inp.url,
source_url=info.get('source_url'), source_title=info.get('title'),
price_cents=info.get('price_cents'), currency=(info.get('currency') or 'EUR'),
image_url=info.get('image_url')))
s.commit(); return {"ok": True}


@app.post("/api/reserve")
def api_reserve(inp: BotIdIn, x_telegram_init: str = Header(None, convert_underscores=True)):
data = verify_init_data(x_telegram_init or ""); tg_user = int(eval(data.get('user', '{}')).get('id')) if 'user' in data else int(data.get('tg_user_id','0') or 0)
with Session(engine) as s:
ga = s.get(GuestActive, tg_user)
if not ga: raise HTTPException(400, "Join a list in the bot first.")
it = s.get(Item, {"wishlist_id": ga.wishlist_id, "bot_id": inp.bot_id})
if not it: raise HTTPException(404, "Item not found")
r = s.get(Reservation, {"wishlist_id": ga.wishlist_id, "bot_id": inp.bot_id})
if r and r.status in ('hidden','received'): raise HTTPException(400, "Unavailable")
if r and r.status=='reserved' and r.user_tg_id!=tg_user: raise HTTPException(409, "Already reserved by someone else")
if not r:
s.add(Reservation(wishlist_id=ga.wishlist_id, bot_id=inp.bot_id, status='reserved', user_tg_id=tg_user))
else:
r.status='reserved'; r.user_tg_id=tg_user; r.updated_at=utcnow()
s.commit(); return {"ok": True}


@app.post("/api/unreserve")
def api_unreserve(inp: BotIdIn, x_telegram_init: str = Header(None, convert_underscores=True)):
data = verify_init_data(x_telegram_init or ""); tg_user = int(eval(data.get('user', '{}')).get('id')) if 'user' in data else int(data.get('tg_user_id','0') or 0)
with Session(engine) as s:
ga = s.get(GuestActive, tg_user)
if not ga: raise HTTPException(400, "Join a list in the bot first.")
r = s.get(Reservation, {"wishlist_id": ga.wishlist_id, "bot_id": inp.bot_id})
if not r or r.status!='reserved' or r.user_tg_id!=tg_user: raise HTTPException(400, "You have no reservation for this item")
r.status='available'; r.user_tg_id=None; r.updated_at=utcnow(); s.commit(); return {"ok": True}
