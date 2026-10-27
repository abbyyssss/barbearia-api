"""Formato dos dados que entram e saem da API (validação com Pydantic)."""
from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Agendamento


class ServicoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    duracao_min: int
    preco: float

    @field_validator("preco", mode="before")
    @classmethod
    def preco_como_numero(cls, valor):
        return float(valor)  # o banco devolve Decimal


class BarbeiroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    especialidade: str | None = None


class HorariosOut(BaseModel):
    data: date
    horarios: list[str]  # ex.: ["09:00", "09:30"]


class AgendamentoIn(BaseModel):
    servico_id: int
    barbeiro_id: int
    data: date
    hora_inicio: time
    nome: str = Field(min_length=2, max_length=100)
    telefone: str

    @field_validator("nome")
    @classmethod
    def limpar_nome(cls, valor: str) -> str:
        valor = " ".join(valor.split())
        if len(valor) < 2:
            raise ValueError("Informe o nome.")
        return valor

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, valor: str) -> str:
        digitos = "".join(c for c in valor if c.isdigit())
        if len(digitos) not in (10, 11):
            raise ValueError("Informe o telefone com DDD.")
        return digitos


class AgendamentoOut(BaseModel):
    id: int
    cliente: str
    telefone: str
    servico: str
    barbeiro: str
    data: date
    hora_inicio: str
    hora_fim: str
    preco: float
    status: str


def montar_saida(item: Agendamento) -> AgendamentoOut:
    """Converte um Agendamento do banco no formato enviado ao site."""
    return AgendamentoOut(
        id=item.id,
        cliente=item.cliente.nome,
        telefone=item.cliente.telefone,
        servico=item.servico.nome,
        barbeiro=item.barbeiro.nome,
        data=item.data,
        hora_inicio=item.hora_inicio.strftime("%H:%M"),
        hora_fim=item.hora_fim.strftime("%H:%M"),
        preco=float(item.preco),
        status=item.status,
    )


class LoginIn(BaseModel):
    email: str
    senha: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"