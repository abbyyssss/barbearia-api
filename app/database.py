"""Conexão com o MySQL e sessão de banco usada pelas rotas."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
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