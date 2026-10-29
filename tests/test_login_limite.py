"""Testes do limite de tentativas de login (app/limite.py)."""
from app import limite
from tests.conftest import ADMIN_EMAIL, ADMIN_SENHA


def errar(client, email=ADMIN_EMAIL, vezes=1):
    for _ in range(vezes):
        resposta = client.post("/login", json={"email": email, "senha": "errada"})
    return resposta


def entrar(client):
    return client.post("/login", json={"email": ADMIN_EMAIL, "senha": ADMIN_SENHA})


def test_bloqueia_depois_de_5_senhas_erradas(client):
    assert errar(client, vezes=5).status_code == 401
    assert errar(client).status_code == 429


def test_bloqueio_vale_ate_para_a_senha_correta(client):
    errar(client, vezes=5)
    resposta = entrar(client)
    assert resposta.status_code == 429
    assert "Retry-After" in resposta.headers


def test_login_correto_zera_o_contador_do_email(client):
    errar(client, vezes=4)
    assert entrar(client).status_code == 200
    assert errar(client, vezes=4).status_code == 401   # recomeçou do zero


def test_outro_email_nao_e_afetado(client):
    errar(client, vezes=5)
    assert errar(client, email="outro@teste.com").status_code == 401


def test_bloqueio_acaba_depois_de_15_minutos(client, monkeypatch):
    errar(client, vezes=5)
    futuro = limite._relogio() + 16 * 60
    monkeypatch.setattr(limite, "_relogio", lambda: futuro)
    assert entrar(client).status_code == 200


def test_limite_por_ip_bloqueia_varios_emails_seguidos(client):
    for numero in range(20):
        errar(client, email=f"alvo{numero}@teste.com")
    assert errar(client, email="novo@teste.com").status_code == 429