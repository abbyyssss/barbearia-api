"""Regras de negócio: expediente, prazo de agendamento e conflito de horários.

É aqui que a API tem a palavra final, mesmo que o site já valide antes.
"""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Agendamento

ABERTURA = 9 * 60          # 09:00 (minutos desde a meia-noite)
FECHAMENTO_SEMANA = 19 * 60
FECHAMENTO_SABADO = 16 * 60
PASSO = 30                 # um horário a cada 30 minutos
DIAS_A_FRENTE = 30


def agora() -> datetime:
    return datetime.now(ZoneInfo(settings.timezone))


def em_minutos(valor: time) -> int:
    return valor.hour * 60 + valor.minute


def em_time(minutos: int) -> time:
    return time(minutos // 60, minutos % 60)


def erro_na_data(dia: date) -> str | None:
    """Devolve a mensagem de erro se a data não puder ser agendada, ou None se estiver ok."""
    hoje = agora().date()
    if dia < hoje:
        return "Não é possível agendar em uma data que já passou."
    if dia > hoje + timedelta(days=DIAS_A_FRENTE):
        return f"Só é possível agendar até {DIAS_A_FRENTE} dias à frente."
    if dia.weekday() == 6:
        return "A barbearia fecha aos domingos."
    return None


def horarios_livres(db: Session, barbeiro_id: int, dia: date, duracao_min: int) -> list[time]:
    """Lista os horários de início possíveis para o barbeiro, no dia, para um serviço dessa duração."""
    if erro_na_data(dia):
        return []

    fechamento = FECHAMENTO_SABADO if dia.weekday() == 5 else FECHAMENTO_SEMANA
    ocupados = [
        (em_minutos(item.hora_inicio), em_minutos(item.hora_fim))
        for item in db.scalars(
            select(Agendamento).where(
                Agendamento.barbeiro_id == barbeiro_id,
                Agendamento.data == dia,
                Agendamento.status == "agendado",
            )
        )
    ]

    agora_local = agora()
    minutos_agora = agora_local.hour * 60 + agora_local.minute
    eh_hoje = dia == agora_local.date()

    livres = []
    inicio = ABERTURA
    while inicio + duracao_min <= fechamento:
        fim = inicio + duracao_min
        # Dois intervalos se sobrepõem quando cada um começa antes de o outro terminar
        conflito = any(inicio < fim_o and ini_o < fim for ini_o, fim_o in ocupados)
        passou = eh_hoje and inicio <= minutos_agora
        if not conflito and not passou:
            livres.append(em_time(inicio))
        inicio += PASSO
    return livres