
from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Usuario
from app.security import gerar_hash

email = input("E-mail atual do administrador: ").strip().lower()
senha = getpass("Nova senha exclusiva da barbearia: ")

if "@" not in email or len(senha) < 12:
    raise SystemExit("E-mail inválido ou senha deve ter pelo menos 12 caracteres.")

with SessionLocal() as db:
    usuario = db.scalar(
        select(Usuario).where(Usuario.email == email)
    )

    if usuario is None:
        raise SystemExit("Administrador não encontrado.")

    usuario.senha_hash = gerar_hash(senha)
    db.commit()

print("Senha do administrador alterada com sucesso!")
