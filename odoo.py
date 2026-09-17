import httpx
from .config import settings
class OdooJSON2:
    async def call(self,model,method,payload):
        if not settings.odoo_api_key: raise RuntimeError('Odoo External API no configurada')
        url=f"{settings.odoo_base_url.rstrip('/')}/json/2/{model}/{method}"
        h={'Authorization':f'Bearer {settings.odoo_api_key}','Content-Type':'application/json'}
        if settings.odoo_db:h['X-Odoo-Database']=settings.odoo_db
        async with httpx.AsyncClient(timeout=30) as c:
            r=await c.post(url,headers=h,json=payload); r.raise_for_status(); return r.json()
