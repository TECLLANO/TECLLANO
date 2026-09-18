import httpx

from config import settings


class OdooJSON2:
    async def call(self, model: str, method: str, payload: dict):
        if not settings.odoo_api_key:
            raise RuntimeError('ODOO_API_KEY no está configurada.')
        url = f'{settings.odoo_base_url.rstrip("/")}/json/2/{model}/{method}'
        headers = {'Authorization': f'Bearer {settings.odoo_api_key}', 'Content-Type': 'application/json'}
        if settings.odoo_db:
            headers['X-Odoo-Database'] = settings.odoo_db
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
