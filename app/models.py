"""Tabelas do banco representadas como classes Python (SQLAlchemy)."""
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Servico(Base):
    __tablename__ = "servicos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    duracao_min: Mapped[int]
    preco: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Barbeiro(Base):
    __tablename__ = "barbeiros"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    especialidade: Mapped[str | None] = mapped_column(String(80))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    telefone: Mapped[str] = mapped_column(String(20), unique=True)


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    servico_id: Mapped[int] = mapped_column(ForeignKey("servicos.id"))
    barbeiro_id: Mapped[int] = mapped_column(ForeignKey("barbeiros.id"))
    data: Mapped[date]
    hora_inicio: Mapped[time]
    hora_fim: Mapped[time]
    preco: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    status: Mapped[str] = mapped_column(
        Enum("agendado", "cancelado", name="status_agendamento"), default="agendado"
    )
    criado_em: Mapped[datetime] = mapped_column(server_default=func.now())

    cliente: Mapped[Cliente] = relationship()
    servico: Mapped[Servico] = relationship()
    barbeiro: Mapped[Barbeiro] = relationship()


class Usuario(Base):
    """Quem pode entrar no painel (o dono ou os barbeiros)."""
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))