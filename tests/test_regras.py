"""Testes das regras de negócio (app/regras.py): datas, expediente e conflitos."""
from datetime import date, datetime, time
from decimal import Decimal

from app import regras
from app.models import Agendamento
from app.regras import PASSO, em_minutos, erro_na_data, horarios_livres
from tests.conftest import AGORA_FIXO, BARBA, CORTE, DIEGO, RAFAEL

SEGUNDA = date(2026, 11, 3)      # dia útil
SABADO = date(2026, 11, 7)
DOMINGO = date(2026, 11, 8)


def agendar(db, barbeiro_id, dia, inicio, fim, status="agendado"):
    db.add(Agendamento(
        cliente_id=1, servico_id=CORTE, barbeiro_id=barbeiro_id, data=dia,
        hora_inicio=inicio, hora_fim=fim, preco=Decimal("55.00"), status=status,
    ))
    db.commit()


# ---------- validação da data ----------

def test_dia_util_dentro_do_prazo_e_aceito():
    assert erro_na_data(SEGUNDA) is None


def test_data_passada_e_recusada():
    assert erro_na_data(date(2026, 11, 1)) is not None


def test_hoje_e_aceito():
    assert erro_na_data(AGORA_FIXO.date()) is None


def test_ultimo_dia_do_prazo_e_aceito_e_o_seguinte_nao():
    assert erro_na_data(date(2026, 12, 2)) is None       # hoje + 30 dias
    assert erro_na_data(date(2026, 12, 3)) is not None   # hoje + 31 dias


def test_domingo_e_recusado():
    assert erro_na_data(DOMINGO) is not None


# ---------- horários livres ----------

def test_dia_vazio_comeca_as_9h_e_termina_antes_do_fechamento(db):
    livres = horarios_livres(db, RAFAEL, SEGUNDA, 45)
    assert livres[0] == time(9, 0)
    assert em_minutos(livres[-1]) + 45 <= 19 * 60       # o serviço termina até as 19h
    assert all(em_minutos(h) % PASSO == 0 for h in livres)


def test_sabado_fecha_as_16h(db):
    livres = horarios_livres(db, RAFAEL, SABADO, 45)
    assert livres
    assert em_minutos(livres[-1]) + 45 <= 16 * 60


def test_domingo_nao_tem_horarios(db):
    assert horarios_livres(db, RAFAEL, DOMINGO, 45) == []


def test_data_passada_nao_tem_horarios(db):
    assert horarios_livres(db, RAFAEL, date(2026, 11, 1), 45) == []


def test_horario_ocupado_bloqueia_quem_invade_o_intervalo(db):
    # Corte das 9:30 às 10:15
    agendar(db, RAFAEL, SEGUNDA, time(9, 30), time(10, 15))
    livres = horarios_livres(db, RAFAEL, SEGUNDA, 45)

    assert time(9, 0) not in livres     # 9:00 + 45 min terminaria às 9:45, invadindo o corte
    assert time(9, 30) not in livres
    assert time(10, 0) not in livres    # começaria antes de o corte terminar
    assert time(10, 30) in livres


def test_servico_que_termina_quando_o_outro_comeca_nao_conflita(db):
    agendar(db, RAFAEL, SEGUNDA, time(9, 30), time(10, 15))
    livres = horarios_livres(db, RAFAEL, SEGUNDA, 30)   # barba: 9:00 às 9:30

    assert time(9, 0) in livres


def test_outro_barbeiro_continua_livre(db):
    agendar(db, RAFAEL, SEGUNDA, time(9, 30), time(10, 15))

    assert time(9, 30) in horarios_livres(db, DIEGO, SEGUNDA, 45)


def test_agendamento_cancelado_nao_bloqueia(db):
    agendar(db, RAFAEL, SEGUNDA, time(9, 30), time(10, 15), status="cancelado")

    assert time(9, 30) in horarios_livres(db, RAFAEL, SEGUNDA, 45)


def test_horarios_que_ja_passaram_hoje_nao_aparecem(db, monkeypatch):
    dez_e_dez = datetime(2026, 11, 2, 10, 10, tzinfo=AGORA_FIXO.tzinfo)
    monkeypatch.setattr(regras, "agora", lambda: dez_e_dez)

    livres = horarios_livres(db, RAFAEL, dez_e_dez.date(), 30)
    assert livres
    assert all(h > time(10, 10) for h in livres)