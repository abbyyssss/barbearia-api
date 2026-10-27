"""Rotas abertas: o cliente consulta serviços e horários e faz o agendamento."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agendamento, Barbeiro, Cliente, Servico
from app.regras import em_minutos, em_time, erro_na_data, horarios_livres
from app.schemas import (
    AgendamentoIn,
    AgendamentoOut,
    BarbeiroOut,
    HorariosOut,
    ServicoOut,
    montar_saida,
)

router = APIRouter(tags=["Público"])


@router.get("/servicos", response_model=list[ServicoOut])
def listar_servicos(db: Session = Depends(get_db)):
    return db.scalars(select(Servico).where(Servico.ativo).order_by(Servico.id)).all()


@router.get("/barbeiros", response_model=list[BarbeiroOut])
def listar_barbeiros(db: Session = Depends(get_db)):
    return db.scalars(select(Barbeiro).where(Barbeiro.ativo).order_by(Barbeiro.id)).all()


@router.get("/horarios", response_model=HorariosOut)
def listar_horarios(
    barbeiro_id: int, servico_id: int, data: date, db: Session = Depends(get_db)
):
    servico = db.get(Servico, servico_id)
    if servico is None or not servico.ativo:
        raise HTTPException(404, "Serviço não encontrado.")

    barbeiro = db.get(Barbeiro, barbeiro_id)
    if barbeiro is None or not barbeiro.ativo:
        raise HTTPException(404, "Barbeiro não encontrado.")

    erro = erro_na_data(data)
    if erro:
        raise HTTPException(400, erro)

    livres = horarios_livres(db, barbeiro_id, data, servico.duracao_min)
    return HorariosOut(data=data, horarios=[h.strftime("%H:%M") for h in livres])


@router.post("/agendamentos", response_model=AgendamentoOut, status_code=201)
def criar_agendamento(dados: AgendamentoIn, db: Session = Depends(get_db)):
    # Trava a linha do barbeiro até o fim da transação. Se duas pessoas tentarem o
    # mesmo horário ao mesmo tempo, a segunda espera aqui e depois já enxerga o horário
    # ocupado. Isso precisa ser a PRIMEIRA consulta, antes de qualquer leitura comum.
    barbeiro = db.scalar(
        select(Barbeiro).where(Barbeiro.id == dados.barbeiro_id, Barbeiro.ativo).with_for_update()
    )
    if barbeiro is None:
        raise HTTPException(404, "Barbeiro não encontrado.")

    servico = db.get(Servico, dados.servico_id)
    if servico is None or not servico.ativo:
        raise HTTPException(404, "Serviço não encontrado.")

    erro = erro_na_data(dados.data)
    if erro:
        raise HTTPException(400, erro)

    livres = horarios_livres(db, barbeiro.id, dados.data, servico.duracao_min)
    if dados.hora_inicio.replace(second=0, microsecond=0) not in livres:
        raise HTTPException(409, "Esse horário não está mais disponível. Escolha outro.")

    cliente = db.scalar(select(Cliente).where(Cliente.telefone == dados.telefone))
    if cliente is None:
        cliente = Cliente(nome=dados.nome, telefone=dados.telefone)
        db.add(cliente)
    else:
        cliente.nome = dados.nome
    db.flush()

    inicio = em_minutos(dados.hora_inicio)
    agendamento = Agendamento(
        cliente_id=cliente.id,
        servico_id=servico.id,
        barbeiro_id=barbeiro.id,
        data=dados.data,
        hora_inicio=em_time(inicio),
        hora_fim=em_time(inicio + servico.duracao_min),
        preco=servico.preco,
        status="agendado",
    )
    db.add(agendamento)
    db.commit()
    db.refresh(agendamento)
    return montar_saida(agendamento)