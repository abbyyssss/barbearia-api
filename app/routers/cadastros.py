"""Cadastro de serviços e barbeiros pelo painel (todas as rotas exigem login).

Nada é apagado: itens "desativados" somem do site, mas continuam no banco,
porque os agendamentos antigos dependem deles.
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Barbeiro, Servico
from app.schemas import (
    BarbeiroAdminOut,
    BarbeiroIn,
    BarbeiroPatch,
    ServicoAdminOut,
    ServicoIn,
    ServicoPatch,
)
from app.security import usuario_logado

router = APIRouter(prefix="/admin", tags=["Cadastros"], dependencies=[Depends(usuario_logado)])


def preco_decimal(valor: float) -> Decimal:
    return Decimal(f"{valor:.2f}")


def nome_ja_existe(db: Session, modelo, nome: str, ignorar_id: int | None = None) -> bool:
    """Confere se já há outro item com o mesmo nome (sem diferenciar maiúsculas)."""
    consulta = select(modelo.id).where(func.lower(modelo.nome) == nome.lower())
    if ignorar_id is not None:
        consulta = consulta.where(modelo.id != ignorar_id)
    return db.scalar(consulta.limit(1)) is not None


def exigir_outro_ativo(db: Session, modelo, item_id: int, rotulo: str) -> None:
    """Impede desativar o último item ativo (o site ficaria sem opções para agendar)."""
    outros = db.scalar(
        select(func.count()).select_from(modelo).where(modelo.ativo.is_(True), modelo.id != item_id)
    )
    if not outros:
        raise HTTPException(409, f"Mantenha pelo menos {rotulo} ativo para o site continuar funcionando.")


def validar_alteracoes(mudancas: dict, campos_obrigatorios: tuple) -> None:
    if not mudancas:
        raise HTTPException(400, "Nenhuma alteração enviada.")
    for campo in campos_obrigatorios:
        if campo in mudancas and mudancas[campo] is None:
            raise HTTPException(400, "Nenhum campo pode ficar vazio.")


# ---------- serviços ----------

@router.get("/servicos", response_model=list[ServicoAdminOut])
def listar_servicos(db: Session = Depends(get_db)):
    """Todos os serviços, inclusive os desativados (ativos primeiro)."""
    return db.scalars(select(Servico).order_by(Servico.ativo.desc(), Servico.id)).all()


@router.post("/servicos", response_model=ServicoAdminOut, status_code=201)
def criar_servico(dados: ServicoIn, db: Session = Depends(get_db)):
    if nome_ja_existe(db, Servico, dados.nome):
        raise HTTPException(409, "Já existe um serviço com esse nome.")
    servico = Servico(
        nome=dados.nome,
        duracao_min=dados.duracao_min,
        preco=preco_decimal(dados.preco),
        ativo=True,
    )
    db.add(servico)
    db.commit()
    db.refresh(servico)
    return servico


@router.patch("/servicos/{servico_id}", response_model=ServicoAdminOut)
def atualizar_servico(servico_id: int, dados: ServicoPatch, db: Session = Depends(get_db)):
    servico = db.get(Servico, servico_id)
    if servico is None:
        raise HTTPException(404, "Serviço não encontrado.")

    mudancas = dados.model_dump(exclude_unset=True)
    validar_alteracoes(mudancas, ("nome", "duracao_min", "preco", "ativo"))

    if "nome" in mudancas and nome_ja_existe(db, Servico, mudancas["nome"], servico.id):
        raise HTTPException(409, "Já existe um serviço com esse nome.")
    if mudancas.get("ativo") is False and servico.ativo:
        exigir_outro_ativo(db, Servico, servico.id, "um serviço")

    if "nome" in mudancas:
        servico.nome = mudancas["nome"]
    if "duracao_min" in mudancas:
        servico.duracao_min = mudancas["duracao_min"]
    if "preco" in mudancas:
        servico.preco = preco_decimal(mudancas["preco"])
    if "ativo" in mudancas:
        servico.ativo = mudancas["ativo"]

    db.commit()
    db.refresh(servico)
    return servico


# ---------- barbeiros ----------

@router.get("/barbeiros", response_model=list[BarbeiroAdminOut])
def listar_barbeiros(db: Session = Depends(get_db)):
    """Todos os barbeiros, inclusive os desativados (ativos primeiro)."""
    return db.scalars(select(Barbeiro).order_by(Barbeiro.ativo.desc(), Barbeiro.id)).all()


@router.post("/barbeiros", response_model=BarbeiroAdminOut, status_code=201)
def criar_barbeiro(dados: BarbeiroIn, db: Session = Depends(get_db)):
    if nome_ja_existe(db, Barbeiro, dados.nome):
        raise HTTPException(409, "Já existe um barbeiro com esse nome.")
    barbeiro = Barbeiro(nome=dados.nome, especialidade=dados.especialidade, ativo=True)
    db.add(barbeiro)
    db.commit()
    db.refresh(barbeiro)
    return barbeiro


@router.patch("/barbeiros/{barbeiro_id}", response_model=BarbeiroAdminOut)
def atualizar_barbeiro(barbeiro_id: int, dados: BarbeiroPatch, db: Session = Depends(get_db)):
    barbeiro = db.get(Barbeiro, barbeiro_id)
    if barbeiro is None:
        raise HTTPException(404, "Barbeiro não encontrado.")

    mudancas = dados.model_dump(exclude_unset=True)
    validar_alteracoes(mudancas, ("nome", "ativo"))   # a especialidade pode ficar vazia

    if "nome" in mudancas and nome_ja_existe(db, Barbeiro, mudancas["nome"], barbeiro.id):
        raise HTTPException(409, "Já existe um barbeiro com esse nome.")
    if mudancas.get("ativo") is False and barbeiro.ativo:
        exigir_outro_ativo(db, Barbeiro, barbeiro.id, "um barbeiro")

    if "nome" in mudancas:
        barbeiro.nome = mudancas["nome"]
    if "especialidade" in mudancas:
        barbeiro.especialidade = mudancas["especialidade"]
    if "ativo" in mudancas:
        barbeiro.ativo = mudancas["ativo"]

    db.commit()
    db.refresh(barbeiro)
    return barbeiro