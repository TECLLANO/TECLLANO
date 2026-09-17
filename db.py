from datetime import datetime, timezone
from sqlalchemy import create_engine,String,Text,Integer,DateTime
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,sessionmaker
from .config import settings
engine=create_engine(settings.database_url,connect_args={'check_same_thread':False} if settings.database_url.startswith('sqlite') else {})
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase): pass
class Credential(Base):
    __tablename__='credentials'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    seller_id:Mapped[str]=mapped_column(String(64),unique=True,index=True)
    access_token_enc:Mapped[str]=mapped_column(Text)
    refresh_token_enc:Mapped[str]=mapped_column(Text)
    expires_at:Mapped[int]=mapped_column(Integer,default=0)
class WebhookEvent(Base):
    __tablename__='webhook_events'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    topic:Mapped[str]=mapped_column(String(80),index=True)
    resource:Mapped[str]=mapped_column(Text)
    user_id:Mapped[str]=mapped_column(String(64),index=True)
    received_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
def init_db(): Base.metadata.create_all(engine)
