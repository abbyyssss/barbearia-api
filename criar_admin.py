"""Cria o usuário que acessa o painel. Rode uma vez:  python criar_admin.py"""
from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Usuario
from app.security import gerar_hash

email = input("E-mail do administrador: ").strip().lower()
senha = getpass("Senha (mínimo 8 caracteres): ")

if "@" not in email or len(senha) < 8:
    raise SystemExit("E-mail inválido ou senha curta demais.")

with SessionLocal() as db:
    if db.scalar(select(Usuario).where(Usuario.email == email)):
        raise SystemExit("Já existe um usuário com esse e-mail.")
    db.add(Usuario(email=email, senha_hash=gerar_hash(senha)))
    db.commit()

print("Administrador criado com sucesso.")