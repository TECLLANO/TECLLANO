# TECLLANO — Mercado Libre ↔ Odoo connector (v0.2)

Servicio FastAPI preparado para Render. El flujo OAuth usa Mercado Libre Colombia (MCO), guarda tokens cifrados y expone endpoints de prueba.

## Render

Build: `pip install -r requirements.txt`

Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Health: `/health`

## Variables obligatorias

- `ML_CLIENT_ID`
- `ML_CLIENT_SECRET`
- `ML_REDIRECT_URI`
- `FERNET_KEY`

`ML_REDIRECT_URI` debe coincidir exactamente con la URI registrada en Mercado Libre.

## Flujo OAuth

Abrir: `/oauth/mercadolibre/start`

Callback: `/oauth/mercadolibre/callback`

Después de autorizar, el servicio consulta `/users/me` y guarda access/refresh tokens cifrados.

## Seguridad

Nunca subas `.env`, client secret, access tokens, refresh tokens o claves de cifrado a GitHub.

## Estado de Odoo

El adaptador JSON-2 queda preparado en `odoo.py`, pero la capacidad de API externa de Odoo debe estar habilitada en el plan/entorno de Odoo antes de activar la sincronización bidireccional.
