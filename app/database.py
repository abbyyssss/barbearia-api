"""Conexão com o MySQL e sessão de banco usada pelas rotas."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# Bancos na nuvem (como o Aiven) só aceitam conexão criptografada
connect_args = {"ssl": {"ca": settings.db_ssl_ca}} if settings.db_ssl_ca else {}

engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Abre uma sessão por requisição e garante que ela seja fechada."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()