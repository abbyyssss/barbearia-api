"""Senhas com hash (bcrypt) e login com token JWT."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Usuario

ALGORITMO = "HS256"
bearer = HTTPBearer()


def gerar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def senha_confere(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())


def criar_token(email: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": email, "exp": expira}, settings.jwt_secret, algorithm=ALGORITMO)


def usuario_logado(
    credenciais: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Use como dependência nas rotas que exigem login."""
    try:
        dados = jwt.decode(credenciais.credentials, settings.jwt_secret, algorithms=[ALGORITMO])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Login inválido ou expirado.")

    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.get("sub")))
    if usuario is None:
        raise HTTPException(status_code=401, detail="Login inválido ou expirado.")
    return usuario