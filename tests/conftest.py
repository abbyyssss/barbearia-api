"""Preparação dos testes: banco SQLite em memória e data fixa.

Os testes NÃO tocam no seu MySQL nem na Aiven: usam um banco temporário
que nasce e morre a cada teste.
"""
import os

# Precisa vir ANTES de importar o app. Variáveis de ambiente têm prioridade sobre o .env.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "segredo-so-para-testes-com-mais-de-32-bytes"
os.environ["DB_SSL_CA"] = ""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Barbeiro, Cliente, Servico, Usuario
from app.security import gerar_hash

ADMIN_EMAIL = "admin@teste.com"
ADMIN_SENHA = "senha-forte-123"

# IDs criados em cada teste (o banco recomeça do zero, então a ordem é sempre esta)
CORTE, BARBA, COMBO = 1, 2, 3          # 45 min, 30 min, 75 min
RAFAEL, DIEGO = 1, 2

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestSession = sessionmaker(bind=engine, autoflush=False)

# "Hoje" nos testes: segunda-feira, 2 de novembro de 2026, 08:00 (horário de Brasília)
AGORA_FIXO = datetime(2026, 11, 2, 8, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))


@pytest.fixture(autouse=True)
def relogio(monkeypatch):
    """Congela a data/hora para os testes não dependerem do dia em que rodam."""
    monkeypatch.setattr("app.regras.agora", lambda: AGORA_FIXO)
    monkeypatch.setattr("app.routers.painel.agora", lambda: AGORA_FIXO)


@pytest.fixture
def db():
    Base.metadata.create_all(engine)
    sessao = TestSession()
    sessao.add_all([
        Servico(nome="Corte clássico", duracao_min=45, preco=Decimal("55.00")),
        Servico(nome="Barba com toalha quente", duracao_min=30, preco=Decimal("40.00")),
        Servico(nome="Corte e barba", duracao_min=75, preco=Decimal("85.00")),
        Barbeiro(nome="Rafael"),
        Barbeiro(nome="Diego"),
        Cliente(nome="Cliente Fixo", telefone="11900000000"),
        Usuario(email=ADMIN_EMAIL, senha_hash=gerar_hash(ADMIN_SENHA)),
    ])
    sessao.commit()
    yield sessao
    sessao.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()