"""Rotas do painel: login do barbeiro e gestão dos agendamentos (exigem login)."""
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app import limite
from app.database import get_db
from app.models import Agendamento, Usuario
from app.regras import agora
from app.schemas import AgendamentoOut, LoginIn, TokenOut, montar_saida
from app.security import criar_token, senha_confere, usuario_logado

router = APIRouter(tags=["Painel"])


def ip_do_cliente(request: Request) -> str:
    """Endereço de quem chamou. Atrás do Render, vem no cabeçalho X-Forwarded-For."""
    encaminhado = request.headers.get("x-forwarded-for")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.client.host if request.client else "desconhecido"


@router.post("/login", response_model=TokenOut)
def login(dados: LoginIn, request: Request, db: Session = Depends(get_db)):
    email = dados.email.strip().lower()
    ip = ip_do_cliente(request)

    # Muitas senhas erradas seguidas: recusa antes mesmo de conferir a senha
    espera = limite.segundos_de_espera(email, ip)
    if espera:
        raise HTTPException(
            status_code=429,
            detail=f"Muitas tentativas. Tente novamente em {ceil(espera / 60)} minuto(s).",
            headers={"Retry-After": str(espera)},
        )

    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    # Mesma mensagem para e-mail ou senha errados, para não revelar quais e-mails existem
    if usuario is None or not senha_confere(dados.senha, usuario.senha_hash):
        limite.registrar_falha(email, ip)
        raise HTTPException(401, "E-mail ou senha incorretos.")

    limite.limpar_email(email)
    return TokenOut(access_token=criar_token(usuario.email))


@router.get("/agendamentos", response_model=list[AgendamentoOut])
def listar_agendamentos(db: Session = Depends(get_db), _: Usuario = Depends(usuario_logado)):
    """Agendamentos ativos, de hoje em diante, em ordem cronológica."""
    itens = db.scalars(
        select(Agendamento)
        .options(
            joinedload(Agendamento.cliente),
            joinedload(Agendamento.servico),
            joinedload(Agendamento.barbeiro),
        )
        .where(Agendamento.status == "agendado", Agendamento.data >= agora().date())
        .order_by(Agendamento.data, Agendamento.hora_inicio)
    ).all()
    return [montar_saida(item) for item in itens]


@router.patch("/agendamentos/{agendamento_id}/cancelar", response_model=AgendamentoOut)
def cancelar_agendamento(
    agendamento_id: int, db: Session = Depends(get_db), _: Usuario = Depends(usuario_logado)
):
    item = db.get(Agendamento, agendamento_id)
    if item is None:
        raise HTTPException(404, "Agendamento não encontrado.")
    if item.status == "cancelado":
        raise HTTPException(409, "Esse agendamento já foi cancelado.")
    item.status = "cancelado"
    db.commit()
    db.refresh(item)
    return montar_saida(item)