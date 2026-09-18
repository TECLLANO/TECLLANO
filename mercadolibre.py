import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode

import httpx
from sqlalchemy import select

from config import settings
from db import Credential, OAuthState, SessionLocal
from security import dec, enc

AUTH = f'https://auth.mercadolibre.com.{"co" if settings.ml_site_id == "MCO" else "com"}/authorization'
TOKEN = 'https://api.mercadolibre.com/oauth/token'
API = 'https://api.mercadolibre.com'


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    return verifier, challenge


def create_oauth_state() -> tuple[str, str | None]:
    state = secrets.token_urlsafe(32)
    verifier = None
    if settings.ml_use_pkce:
        verifier, _ = pkce_pair()
    with SessionLocal() as db:
        db.add(OAuthState(state=state, code_verifier=verifier))
        db.commit()
    return state, verifier


def consume_oauth_state(state: str) -> str | None:
    with SessionLocal() as db:
        row = db.scalar(select(OAuthState).where(OAuthState.state == state))
        if not row:
            return None
        verifier = row.code_verifier
        db.delete(row)
        db.commit()
        return verifier


def auth_url(state: str, code_verifier: str | None = None) -> str:
    params = {
        'response_type': 'code',
        'client_id': settings.ml_client_id,
        'redirect_uri': settings.ml_redirect_uri,
        'state': state,
    }
    if settings.ml_use_pkce:
        if not code_verifier:
            raise RuntimeError('PKCE activo pero falta code_verifier.')
        digest = hashlib.sha256(code_verifier.encode()).digest()
        params['code_challenge'] = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
        params['code_challenge_method'] = 'S256'
    return AUTH + '?' + urlencode(params)


async def exchange(code: str, code_verifier: str | None = None) -> dict:
    if not settings.ml_client_secret:
        raise RuntimeError('ML_CLIENT_SECRET no está configurado.')
    data = {
        'grant_type': 'authorization_code',
        'client_id': settings.ml_client_id,
        'client_secret': settings.ml_client_secret,
        'code': code,
        'redirect_uri': settings.ml_redirect_uri,
    }
    if settings.ml_use_pkce:
        data['code_verifier'] = code_verifier or ''
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(TOKEN, data=data)
        response.raise_for_status()
        return response.json()


async def store_token(token_data: dict) -> dict:
    access_token = token_data['access_token']
    refresh_token = token_data.get('refresh_token', '')
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(API + '/users/me', headers={'Authorization': f'Bearer {access_token}'})
        response.raise_for_status()
        seller = response.json()
    seller_id = str(seller['id'])
    with SessionLocal() as db:
        row = db.scalar(select(Credential).where(Credential.seller_id == seller_id))
        if not row:
            row = Credential(seller_id=seller_id, access_token_enc='', refresh_token_enc='')
            db.add(row)
        row.access_token_enc = enc(access_token)
        if refresh_token:
            row.refresh_token_enc = enc(refresh_token)
        row.expires_at = int(time.time()) + int(token_data.get('expires_in', 21600))
        db.commit()
    return seller


async def refresh(seller_id: str) -> str:
    if not settings.ml_client_secret:
        raise RuntimeError('ML_CLIENT_SECRET no está configurado.')
    with SessionLocal() as db:
        row = db.scalar(select(Credential).where(Credential.seller_id == seller_id))
        refresh_token = dec(row.refresh_token_enc) if row and row.refresh_token_enc else None
    if not refresh_token:
        raise RuntimeError('Seller no autorizado o refresh token inexistente.')
    data = {
        'grant_type': 'refresh_token',
        'client_id': settings.ml_client_id,
        'client_secret': settings.ml_client_secret,
        'refresh_token': refresh_token,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(TOKEN, data=data)
        response.raise_for_status()
        token_data = response.json()
    new_refresh = token_data.get('refresh_token', refresh_token)
    with SessionLocal() as db:
        row = db.scalar(select(Credential).where(Credential.seller_id == seller_id))
        row.access_token_enc = enc(token_data['access_token'])
        row.refresh_token_enc = enc(new_refresh)
        row.expires_at = int(time.time()) + int(token_data.get('expires_in', 21600))
        db.commit()
    return token_data['access_token']


async def token(seller_id: str) -> str:
    with SessionLocal() as db:
        row = db.scalar(select(Credential).where(Credential.seller_id == seller_id))
        if row and row.expires_at > int(time.time()) + 120:
            return dec(row.access_token_enc)
    return await refresh(seller_id)


async def get(seller_id: str, path: str, params: dict | None = None):
    access_token = await token(seller_id)
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(API + path, headers={'Authorization': f'Bearer {access_token}'}, params=params)
        if response.status_code == 401:
            access_token = await refresh(seller_id)
            response = await client.get(API + path, headers={'Authorization': f'Bearer {access_token}'}, params=params)
        response.raise_for_status()
        return response.json()
