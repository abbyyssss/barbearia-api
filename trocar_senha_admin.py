"""Troca a senha do administrador do painel.

Uso (com o ambiente virtual ativo, dentro da pasta do projeto):
    python trocar_senha_admin.py

O e-mail e a senha são digitados no terminal. Nada fica escrito neste arquivo.
O banco usado é o do arquivo .env (para mudar a senha da API publicada,
o .env precisa estar apontando para o banco da Aiven).
"""
from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Usuario
from app.security import gerar_hash

email = input("E-mail atual do administrador: ").strip().lower()
senha = getpass("Nova senha exclusiva da barbearia: ")
confirma = getpass("Repita a nova senha: ")

if senha != confirma:
    raise SystemExit("As senhas não conferem. Nada foi alterado.")
if "@" not in email or len(senha) < 12:
    raise SystemExit("E-mail inválido ou senha com menos de 12 caracteres. Nada foi alterado.")

with SessionLocal() as db:
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))

    if usuario is None:
        raise SystemExit("Administrador não encontrado.")

    usuario.senha_hash = gerar_hash(senha)
    db.commit()

print("Senha do administrador alterada com sucesso!")