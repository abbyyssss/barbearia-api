"""Ponto de entrada da API da Navalha & Co."""
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.routers import painel, publico

app = FastAPI(title="Navalha & Co. – API de agendamento", version="1.0.0")

# Permite que o site (em outro endereço) chame a API pelo navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(publico.router)
app.include_router(painel.router)


@app.get("/", tags=["Status"])
def status():
    return {"status": "ok", "api": "Navalha & Co."}


@app.get("/saude", tags=["Status"])
def saude(db: Session = Depends(get_db)):
    """Confere se a API e o banco de dados estão respondendo.

    Serve para monitoramento: um serviço externo chama esta rota de tempos em
    tempos e avisa por e-mail se ela deixar de responder (código 503).
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")
    return {"status": "ok", "banco": "ok"}