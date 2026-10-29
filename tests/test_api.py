"""Testes das rotas da API, de ponta a ponta (com banco temporário)."""
from tests.conftest import ADMIN_EMAIL, ADMIN_SENHA, BARBA, CORTE, RAFAEL


def pedido(**mudancas):
    dados = {
        "servico_id": CORTE,
        "barbeiro_id": RAFAEL,
        "data": "2026-11-03",
        "hora_inicio": "09:30",
        "nome": "Cliente Teste",
        "telefone": "(11) 91234-5678",
    }
    dados.update(mudancas)
    return dados


def login(client):
    resposta = client.post("/login", json={"email": ADMIN_EMAIL, "senha": ADMIN_SENHA})
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


# ---------- rotas públicas ----------

def test_saude_confirma_api_e_banco(client):
    resposta = client.get("/saude")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


def test_lista_servicos_e_barbeiros(client):
    assert len(client.get("/servicos").json()) == 3
    assert len(client.get("/barbeiros").json()) == 2


def test_horarios_do_dia_comecam_as_9h(client):
    resposta = client.get(
        "/horarios", params={"barbeiro_id": RAFAEL, "servico_id": CORTE, "data": "2026-11-03"}
    )
    assert resposta.status_code == 200
    assert resposta.json()["horarios"][0] == "09:00"


def test_cria_agendamento(client):
    resposta = client.post("/agendamentos", json=pedido())
    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["hora_inicio"] == "09:30"
    assert dados["hora_fim"] == "10:15"
    assert dados["status"] == "agendado"


def test_mesmo_horario_duas_vezes_da_conflito(client):
    assert client.post("/agendamentos", json=pedido()).status_code == 201
    assert client.post("/agendamentos", json=pedido(nome="Outra Pessoa")).status_code == 409


def test_horario_dentro_de_outro_agendamento_da_conflito(client):
    client.post("/agendamentos", json=pedido())                      # 9:30 às 10:15
    resposta = client.post(
        "/agendamentos", json=pedido(servico_id=BARBA, hora_inicio="10:00")
    )
    assert resposta.status_code == 409


def test_data_passada_e_recusada(client):
    assert client.post("/agendamentos", json=pedido(data="2026-11-01")).status_code == 400


def test_domingo_e_recusado(client):
    assert client.post("/agendamentos", json=pedido(data="2026-11-08")).status_code == 400


def test_data_distante_demais_e_recusada(client):
    assert client.post("/agendamentos", json=pedido(data="2030-01-04")).status_code == 400


def test_telefone_invalido_e_recusado(client):
    assert client.post("/agendamentos", json=pedido(telefone="123")).status_code == 422


# ---------- painel (exige login) ----------

def test_painel_sem_login_e_bloqueado(client):
    assert client.get("/agendamentos").status_code in (401, 403)


def test_login_com_senha_errada_e_recusado(client):
    resposta = client.post("/login", json={"email": ADMIN_EMAIL, "senha": "errada"})
    assert resposta.status_code == 401


def test_lista_agendamentos_logado(client):
    client.post("/agendamentos", json=pedido())
    resposta = client.get("/agendamentos", headers=login(client))
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_cancelar_libera_o_horario(client):
    criado = client.post("/agendamentos", json=pedido()).json()
    cabecalho = login(client)

    assert client.patch(f"/agendamentos/{criado['id']}/cancelar", headers=cabecalho).status_code == 200
    # Cancelar duas vezes não faz sentido
    assert client.patch(f"/agendamentos/{criado['id']}/cancelar", headers=cabecalho).status_code == 409
    # O horário voltou a ficar livre
    assert client.post("/agendamentos", json=pedido()).status_code == 201