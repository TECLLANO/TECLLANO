from cryptography.fernet import Fernet
from .config import settings
f=Fernet(settings.fernet_key.encode())
def enc(v:str)->str:return f.encrypt(v.encode()).decode()
def dec(v:str)->str:return f.decrypt(v.encode()).decode()
