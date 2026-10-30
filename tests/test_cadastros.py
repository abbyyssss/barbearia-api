"""Testes do cadastro de serviços e barbeiros (rotas /admin)."""
from tests.conftest import ADMIN_EMAIL, ADMIN_SENHA, BARBA, CORTE, COMBO, DIEGO, RAFAEL


def cabecalho(client):
    resposta = client.post("/login", json={"email": ADMIN_EMAIL, "senha": ADMIN_SENHA})
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def novo_servico(**mudancas):
    dados = {"nome": "Hidratação capilar", "duracao_min": 30, "preco": 35.5}
    dados.update(mudancas)
    return dados


def agendamento():
    return {
        "servico_id": CORTE, "barbeiro_id": RAFAEL, "data": "2026-11-03",
        "hora_inicio": "09:30", "nome": "Cliente Teste", "telefone": "(11) 91234-5678",
    }


def nomes(resposta):
    return [item["nome"] for item in resposta.json()]


# ---------- acesso ----------

def test_rotas_de_cadastro_exigem_login(client):
    for caminho in ("/admin/servicos", "/admin/barbeiros"):
        assert client.get(caminho).status_code in (401, 403)
        assert client.post(caminho, json={}).status_code in (401, 403)
    assert client.patch("/admin/servicos/1", json={"ativo": False}).status_code in (401, 403)


# ---------- serviços ----------

def test_cria_servico_e_ele_aparece_no_site(client):
    resposta = client.post("/admin/servicos", json=novo_servico(), headers=cabecalho(client))
    assert resposta.status_code == 201
    assert resposta.json()["ativo"] is True
    assert resposta.json()["preco"] == 35.5
    assert "Hidratação capilar" in nomes(client.get("/servicos"))


def test_nome_de_servico_repetido_e_recusado(client):
    resposta = client.post(
        "/admin/servicos", json=novo_servico(nome="corte clássico"), headers=cabecalho(client)
    )
    assert resposta.status_code == 409


def test_servico_com_dados_invalidos_e_recusado(client):
    cab = cabecalho(client)
    for invalido in (
        {"duracao_min": 17},     # não é múltiplo de 5
        {"duracao_min": 10},     # curto demais
        {"duracao_min": 300},    # longo demais
        {"preco": 0},
        {"preco": -5},
        {"nome": "A"},
    ):
        resposta = client.post("/admin/servicos", json=novo_servico(**invalido), headers=cab)
        assert resposta.status_code == 422, invalido


def test_edita_preco_e_duracao_do_servico(client):
    resposta = client.patch(
        f"/admin/servicos/{CORTE}", json={"preco": 60, "duracao_min": 50}, headers=cabecalho(client)
    )
    assert resposta.status_code == 200
    assert resposta.json()["preco"] == 60.0
    assert resposta.json()["duracao_min"] == 50


def test_alteracao_vazia_ou_com_campo_nulo_e_recusada(client):
    cab = cabecalho(client)
    assert client.patch(f"/admin/servicos/{CORTE}", json={}, headers=cab).status_code == 400
    assert client.patch(f"/admin/servicos/{CORTE}", json={"nome": None}, headers=cab).status_code == 400


def test_servico_inexistente_da_404(client):
    resposta = client.patch("/admin/servicos/999", json={"ativo": False}, headers=cabecalho(client))
    assert resposta.status_code == 404


def test_servico_desativado_some_do_site_mas_fica_no_painel(client):
    cab = cabecalho(client)
    assert client.patch(f"/admin/servicos/{CORTE}", json={"ativo": False}, headers=cab).status_code == 200

    assert "Corte clássico" not in nomes(client.get("/servicos"))
    painel = client.get("/admin/servicos", headers=cab).json()
    corte = next(item for item in painel if item["id"] == CORTE)
    assert corte["ativo"] is False
    # E não dá mais para agendar com ele
    assert client.post("/agendamentos", json=agendamento()).status_code == 404


def test_nao_desativa_o_ultimo_servico_ativo(client):
    cab = cabecalho(client)
    assert client.patch(f"/admin/servicos/{CORTE}", json={"ativo": False}, headers=cab).status_code == 200
    assert client.patch(f"/admin/servicos/{BARBA}", json={"ativo": False}, headers=cab).status_code == 200
    assert client.patch(f"/admin/servicos/{COMBO}", json={"ativo": False}, headers=cab).status_code == 409


def test_reativa_servico(client):
    cab = cabecalho(client)
    client.patch(f"/admin/servicos/{CORTE}", json={"ativo": False}, headers=cab)
    client.patch(f"/admin/servicos/{CORTE}", json={"ativo": True}, headers=cab)
    assert "Corte clássico" in nomes(client.get("/servicos"))


def test_agendamento_antigo_continua_no_painel_depois_de_desativar_o_servico(client):
    cab = cabecalho(client)
    assert client.post("/agendamentos", json=agendamento()).status_code == 201
    client.patch(f"/admin/servicos/{CORTE}", json={"ativo": False}, headers=cab)

    lista = client.get("/agendamentos", headers=cab).json()
    assert len(lista) == 1
    assert lista[0]["servico"] == "Corte clássico"


# ---------- barbeiros ----------

def test_cria_barbeiro_e_ele_aparece_no_site(client):
    resposta = client.post(
        "/admin/barbeiros", json={"nome": "Caio", "especialidade": "Barba"}, headers=cabecalho(client)
    )
    assert resposta.status_code == 201
    assert "Caio" in nomes(client.get("/barbeiros"))


def test_especialidade_vazia_fica_sem_especialidade(client):
    resposta = client.post(
        "/admin/barbeiros", json={"nome": "Caio", "especialidade": "   "}, headers=cabecalho(client)
    )
    assert resposta.status_code == 201
    assert resposta.json()["especialidade"] is None


def test_nome_de_barbeiro_repetido_e_recusado(client):
    resposta = client.post("/admin/barbeiros", json={"nome": "rafael"}, headers=cabecalho(client))
    assert resposta.status_code == 409


def test_edita_especialidade_do_barbeiro(client):
    cab = cabecalho(client)
    resposta = client.patch(
        f"/admin/barbeiros/{RAFAEL}", json={"especialidade": "Navalha"}, headers=cab
    )
    assert resposta.status_code == 200
    assert resposta.json()["especialidade"] == "Navalha"
    # Esvaziar o campo é permitido
    resposta = client.patch(f"/admin/barbeiros/{RAFAEL}", json={"especialidade": ""}, headers=cab)
    assert resposta.status_code == 200
    assert resposta.json()["especialidade"] is None


def test_barbeiro_desativado_some_do_site_e_nao_recebe_agendamento(client):
    cab = cabecalho(client)
    assert client.patch(f"/admin/barbeiros/{RAFAEL}", json={"ativo": False}, headers=cab).status_code == 200

    assert "Rafael" not in nomes(client.get("/barbeiros"))
    assert client.post("/agendamentos", json=agendamento()).status_code == 404


def test_nao_desativa_o_ultimo_barbeiro_ativo(client):
    cab = cabecalho(client)
    assert client.patch(f"/admin/barbeiros/{RAFAEL}", json={"ativo": False}, headers=cab).status_code == 200
    assert client.patch(f"/admin/barbeiros/{DIEGO}", json={"ativo": False}, headers=cab).status_code == 409