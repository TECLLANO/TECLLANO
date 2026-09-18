from cryptography.fernet import Fernet

from config import settings


def _fernet() -> Fernet:
    if not settings.fernet_key:
        raise RuntimeError('FERNET_KEY no está configurada en el servidor.')
    return Fernet(settings.fernet_key.encode())


def enc(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def dec(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()
