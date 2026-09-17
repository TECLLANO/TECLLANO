import secrets
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from .db import init_db,SessionLocal,WebhookEvent
from .mercadolibre import auth_url,exchange,store_token,get
app=FastAPI(title='TECLLANO Mercado Libre Connector',version='0.1.0')
init_db(); states=set()
@app.get('/health')
async def health():return {'status':'ok','version':'0.1.0'}
@app.get('/oauth/mercadolibre/start')
async def start():
    s=secrets.token_urlsafe(32); states.add(s); return RedirectResponse(auth_url(s))
@app.get('/oauth/mercadolibre/callback')
async def callback(code:str,state:str):
    if state not in states:raise HTTPException(400,'OAuth state inválido')
    states.remove(state); me=await store_token(await exchange(code)); return {'status':'authorized','seller_id':str(me['id']),'nickname':me.get('nickname')}
@app.get('/meli/{seller_id}/me')
async def me(seller_id:str):return await get(seller_id,'/users/me')
@app.get('/meli/{seller_id}/items')
async def items(seller_id:str,user_id:str,offset:int=0,limit:int=50):return await get(seller_id,f'/users/{user_id}/items/search',{'offset':offset,'limit':limit})
@app.get('/meli/{seller_id}/item/{item_id}')
async def item(seller_id:str,item_id:str):return await get(seller_id,f'/items/{item_id}')
@app.get('/meli/{seller_id}/orders/{order_id}')
async def order(seller_id:str,order_id:str):return await get(seller_id,f'/orders/{order_id}')
@app.post('/webhooks/mercadolibre')
async def webhook(request:Request):
    p=await request.json()
    with SessionLocal() as db:db.add(WebhookEvent(topic=p.get('topic',''),resource=p.get('resource',''),user_id=str(p.get('user_id',''))));db.commit()
    return {'received':True}
@app.get('/admin/webhooks')
async def webhooks(limit:int=50):
    with SessionLocal() as db:
        rows=db.scalars(select(WebhookEvent).order_by(WebhookEvent.id.desc()).limit(limit)).all()
        return [{'id':x.id,'topic':x.topic,'resource':x.resource,'user_id':x.user_id} for x in rows]
