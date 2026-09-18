from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from config import settings
from db import SessionLocal, WebhookEvent, init_db
from mercadolibre import auth_url, consume_oauth_state, create_oauth_state, exchange, get, store_token

app = FastAPI(title='TECLLANO Mercado Libre Connector', version='0.2.0')
init_db()


@app.get('/')
async def root():
    return {'service': 'TECLLANO Mercado Libre Connector', 'status': 'ok', 'version': '0.2.0'}


@app.get('/health')
async def health():
    return {'status': 'ok', 'version': '0.2.0', 'site_id': settings.ml_site_id}


@app.get('/oauth/mercadolibre/start')
async def oauth_start():
    if not settings.ml_client_id or not settings.ml_redirect_uri:
        raise HTTPException(status_code=503, detail='Mercado Libre OAuth no está configurado: faltan ML_CLIENT_ID o ML_REDIRECT_URI.')
    state, verifier = create_oauth_state()
    return RedirectResponse(auth_url(state, verifier))


@app.get('/oauth/mercadolibre/callback')
async def oauth_callback(code: str, state: str):
    verifier = consume_oauth_state(state)
    if verifier is None:
        raise HTTPException(status_code=400, detail='OAuth state inválido o ya utilizado.')
    seller = await store_token(await exchange(code, verifier))
    return {'status': 'authorized', 'seller_id': str(seller['id']), 'nickname': seller.get('nickname')}


@app.get('/meli/{seller_id}/me')
async def me(seller_id: str):
    return await get(seller_id, '/users/me')


@app.get('/meli/{seller_id}/items')
async def items(seller_id: str, user_id: str, offset: int = 0, limit: int = 50):
    return await get(seller_id, f'/users/{user_id}/items/search', {'offset': offset, 'limit': limit})


@app.get('/meli/{seller_id}/item/{item_id}')
async def item(seller_id: str, item_id: str):
    return await get(seller_id, f'/items/{item_id}')


@app.get('/meli/{seller_id}/orders/{order_id}')
async def order(seller_id: str, order_id: str):
    return await get(seller_id, f'/orders/{order_id}')


@app.post('/webhooks/mercadolibre')
async def webhook(request: Request):
    payload = await request.json()
    with SessionLocal() as db:
        db.add(WebhookEvent(topic=str(payload.get('topic', '')), resource=str(payload.get('resource', '')), user_id=str(payload.get('user_id', ''))))
        db.commit()
    return {'received': True}


@app.get('/admin/webhooks')
async def webhooks(limit: int = 50):
    with SessionLocal() as db:
        rows = db.scalars(select(WebhookEvent).order_by(WebhookEvent.id.desc()).limit(min(limit, 200))).all()
        return [{'id': x.id, 'topic': x.topic, 'resource': x.resource, 'user_id': x.user_id, 'received_at': x.received_at.isoformat()} for x in rows]
