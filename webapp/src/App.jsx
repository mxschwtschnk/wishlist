import React, { useEffect, useState } from 'react'
async function api(path, method='GET', body){
const base = import.meta.env.VITE_API_BASE
const headers = {'Content-Type':'application/json'}
if (tg?.initData) headers['X-Telegram-Init'] = tg.initData
const res = await fetch(`${base}${path}`, {method, headers, body: body? JSON.stringify(body): undefined})
if(!res.ok) throw new Error(await res.text())
return await res.json()
}
export default function App(){
const [items,setItems] = useState([])
const [loading,setLoading] = useState(true)
const [error,setError] = useState(null)
const [isOwner,setIsOwner] = useState(false)
const [addUrl,setAddUrl] = useState('')


useEffect(()=>{
tg?.ready(); tg?.expand();
load()
},[])


async function load(){
setLoading(true); setError(null)
try{ const data = await api('/api/view'); setItems(data.items||[]); setIsOwner(!!data.is_owner) }
catch(e){ setError('Failed to load the list.') }
finally{ setLoading(false) }
}
async function reserve(id){ try{ await api('/api/reserve','POST',{bot_id:id}); load() } catch{ setError('Reservation error.') } }
async function unreserve(id){ try{ await api('/api/unreserve','POST',{bot_id:id}); load() } catch{ setError('Unreserve error.') } }
async function add(){ if(!addUrl.trim()) return; try{ await api('/api/addurl','POST',{url:addUrl.trim()}); setAddUrl(''); load() } catch{ setError('Failed to add by URL.') } }


return (
<div style={{minHeight:'100vh',padding:'16px'}}>
<div style={{maxWidth:720, margin:'0 auto'}}>
<header style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
<h1 style={{fontSize:20, margin:0}}>🎁 Wishlist</h1>
{isOwner && <span style={{fontSize:12, padding:'4px 8px',borderRadius:999, background:'#111', color:'#fff'}}>Owner</span>}
</header>


{isOwner && (
<div style={{background:'#fff',borderRadius:16,padding:12,boxShadow:'0 1px 4px rgba(0,0,0,0.08)',marginBottom:12}}>
<div style={{fontSize:14,fontWeight:600,marginBottom:8}}>Add by URL</div>
<div style={{display:'flex', gap:8}}>
<input value={addUrl} onChange={e=>setAddUrl(e.target.value)} placeholder="https://store/product" style={{flex:1,padding:'10px 12px',border:'1px solid #ddd',borderRadius:12}} />
<button onClick={add} style={{padding:'10px 16px',borderRadius:12, background:'#111', color:'#fff', border:'none'}}>Add</button>
</div>
<div style={{fontSize:12,color:'#666',marginTop:6}}>Title, price and image will be fetched automatically.</div>
</div>
)}


{loading && <div>Loading…</div>}
{error && <div style={{color:'#b00020'}}>{error}</div>}
{!loading && !items.length && <div style={{color:'#666'}}>No items yet.</div>}


<div style={{display:'grid', gap:12}}>
{items.map(it => (
<div key={it.bot_id} style={{background:'#fff',borderRadius:16,overflow:'hidden',boxShadow:'0 1px 4px rgba(0,0,0,0.08)'}}>
{it.image_url && <img src={it.image_url} alt={it.title} style={{width:'100%',height:180,objectFit:'cover'}}/>}
<div style={{padding:12}}>
<div style={{fontWeight:600}}>{it.title}</div>
<div style={{fontSize:14,color:'#666'}}>{formatPrice(it.price_cents,it.currency)}</div>
<a href={it.url} target="_blank" rel="noreferrer" style={{display:'inline-block',fontSize:14, color:'#06f', textDecoration:'underline',wordBreak:'break-all'}}>{it.url}</a>
<div style={{marginTop:8}}>
{it.mine
? <button onClick={()=>unreserve(it.bot_id)} style={{width:'100%',padding:'10px 16px',borderRadius:12,border:'1px solid #ddd',background:'#fff'}}>Unreserve</button>
: <button onClick={()=>reserve(it.bot_id)} style={{width:'100%',padding:'10px 16px',borderRadius:12,border:'none',background:'#111',color:'#fff'}}>Reserve</button>}
</div>
</div>
</div>
))}
</div>


<div style={{textAlign:'center',fontSize:12,color:'#888',padding:'24px 0'}}>Telegram Mini App · Wishlist</div>
</div>
</div>
)
}
