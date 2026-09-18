from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    ml_client_id: str = ''
    ml_client_secret: str = ''
    ml_redirect_uri: str = ''
    ml_site_id: str = 'MCO'
    ml_use_pkce: bool = False
    database_url: str = 'sqlite:///./connector.db'
    fernet_key: str = ''
    odoo_base_url: str = 'https://tecnocardellano.odoo.com'
    odoo_api_key: str = ''
    odoo_db: str = ''
    app_env: str = 'production'
    webhook_secret: str = ''


settings = Settings()
