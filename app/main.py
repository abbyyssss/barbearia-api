"""Ponto de entrada da API da Navalha & Co."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
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