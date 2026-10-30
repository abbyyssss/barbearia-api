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


class ServicoAdminOut(ServicoOut):
    ativo: bool


class BarbeiroAdminOut(BarbeiroOut):
    ativo: bool


def _limpar_texto(valor: str) -> str:
    return " ".join(valor.split())


def _nome_valido(valor: str | None, rotulo: str) -> str | None:
    if valor is None:
        return None
    valor = _limpar_texto(valor)
    if len(valor) < 2:
        raise ValueError(f"Informe o nome do {rotulo}.")
    return valor


def _duracao_valida(valor: int | None) -> int | None:
    if valor is not None and valor % 5:
        raise ValueError("A duração deve ser um múltiplo de 5 minutos.")
    return valor


def _especialidade_valida(valor: str | None) -> str | None:
    if valor is None:
        return None
    return _limpar_texto(valor) or None   # texto vazio vira "sem especialidade"


class ServicoIn(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    duracao_min: int = Field(ge=15, le=240)
    preco: float = Field(gt=0, le=10000)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor):
        return _nome_valido(valor, "serviço")

    @field_validator("duracao_min")
    @classmethod
    def validar_duracao(cls, valor):
        return _duracao_valida(valor)


class ServicoPatch(BaseModel):
    """Só os campos enviados são alterados."""
    nome: str | None = Field(default=None, min_length=2, max_length=80)
    duracao_min: int | None = Field(default=None, ge=15, le=240)
    preco: float | None = Field(default=None, gt=0, le=10000)
    ativo: bool | None = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor):
        return _nome_valido(valor, "serviço")

    @field_validator("duracao_min")
    @classmethod
    def validar_duracao(cls, valor):
        return _duracao_valida(valor)


class BarbeiroIn(BaseModel):
    nome: str = Field(min_length=2, max_length=60)
    especialidade: str | None = Field(default=None, max_length=80)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor):
        return _nome_valido(valor, "barbeiro")

    @field_validator("especialidade")
    @classmethod
    def validar_especialidade(cls, valor):
        return _especialidade_valida(valor)


class BarbeiroPatch(BaseModel):
    """Só os campos enviados são alterados. Especialidade vazia apaga o texto."""
    nome: str | None = Field(default=None, min_length=2, max_length=60)
    especialidade: str | None = Field(default=None, max_length=80)
    ativo: bool | None = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor):
        return _nome_valido(valor, "barbeiro")

    @field_validator("especialidade")
    @classmethod
    def validar_especialidade(cls, valor):
        return _especialidade_valida(valor)


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