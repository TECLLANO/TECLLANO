import time,httpx
from urllib.parse import urlencode
from sqlalchemy import select
from .config import settings
from .db import SessionLocal,Credential
from .security import enc,dec
AUTH='https://auth.mercadolibre.com.co/authorization'; TOKEN='https://api.mercadolibre.com/oauth/token'; API='https://api.mercadolibre.com'
def auth_url(state:str)->str:
    return AUTH+'?'+urlencode({'response_type':'code','client_id':settings.ml_client_id,'redirect_uri':settings.ml_redirect_uri,'state':state})
async def exchange(code:str):
    data={'grant_type':'authorization_code','client_id':settings.ml_client_id,'client_secret':settings.ml_client_secret,'code':code,'redirect_uri':settings.ml_redirect_uri}
    async with httpx.AsyncClient(timeout=30) as c:
        r=await c.post(TOKEN,data=data); r.raise_for_status(); return r.json()
async def store_token(t:dict):
    async with httpx.AsyncClient(timeout=30) as c:
        r=await c.get(API+'/users/me',headers={'Authorization':f"Bearer {t['access_token']}"}); r.raise_for_status(); me=r.json()
    sid=str(me['id'])
    with SessionLocal() as db:
        row=db.scalar(select(Credential).where(Credential.seller_id==sid))
        if not row: row=Credential(seller_id=sid,access_token_enc='',refresh_token_enc=''); db.add(row)
        row.access_token_enc=enc(t['access_token']); row.refresh_token_enc=enc(t['refresh_token']); row.expires_at=int(time.time())+int(t.get('expires_in',21600)); db.commit()
    return me
async def refresh(seller_id:str):
    with SessionLocal() as db:
        row=db.scalar(select(Credential).where(Credential.seller_id==seller_id)); refresh_token=dec(row.refresh_token_enc) if row else None
    if not refresh_token: raise RuntimeError('Seller no autorizado')
    data={'grant_type':'refresh_token','client_id':settings.ml_client_id,'client_secret':settings.ml_client_secret,'refresh_token':refresh_token}
    async with httpx.AsyncClient(timeout=30) as c:
        r=await c.post(TOKEN,data=data); r.raise_for_status(); t=r.json()
    with SessionLocal() as db:
        row=db.scalar(select(Credential).where(Credential.seller_id==seller_id)); row.access_token_enc=enc(t['access_token']); row.refresh_token_enc=enc(t.get('refresh_token',refresh_token)); row.expires_at=int(time.time())+int(t.get('expires_in',21600)); db.commit()
    return t['access_token']
async def token(seller_id:str):
    with SessionLocal() as db:
        row=db.scalar(select(Credential).where(Credential.seller_id==seller_id))
        if row and row.expires_at>int(time.time())+120:return dec(row.access_token_enc)
    return await refresh(seller_id)
async def get(seller_id,path,params=None):
    t=await token(seller_id)
    async with httpx.AsyncClient(timeout=30) as c:
        r=await c.get(API+path,headers={'Authorization':f'Bearer {t}'},params=params)
        if r.status_code==401:
            t=await refresh(seller_id); r=await c.get(API+path,headers={'Authorization':f'Bearer {t}'},params=params)
        r.raise_for_status(); return r.json()
