"""Limite de tentativas de login (protege o painel contra tentativas em sequência).

Como funciona: cada senha errada é anotada, por e-mail e por endereço (IP).
Passou do máximo dentro da janela de tempo, o login é recusado (erro 429),
mesmo que a senha esteja certa, até a janela esvaziar.

Limitação: as anotações ficam na memória do servidor. Se a API reiniciar ou
"dormir" (plano gratuito), o contador zera. Para algo mais rígido, o próximo
passo seria guardar as tentativas no banco de dados.
"""
import time
from collections import deque
from threading import Lock

JANELA_SEGUNDOS = 15 * 60
MAX_FALHAS_POR_EMAIL = 5
MAX_FALHAS_POR_IP = 20

_relogio = time.monotonic          # em função própria para os testes poderem "avançar o tempo"
_falhas: dict[str, deque] = {}
_trava = Lock()


def _chaves(email: str, ip: str):
    return ((f"email:{email}", MAX_FALHAS_POR_EMAIL), (f"ip:{ip}", MAX_FALHAS_POR_IP))


def _falhas_recentes(chave: str, agora: float) -> deque:
    """Devolve as falhas ainda dentro da janela, descartando as antigas."""
    fila = _falhas.get(chave)
    if fila is None:
        return deque()
    while fila and agora - fila[0] > JANELA_SEGUNDOS:
        fila.popleft()
    if not fila:
        del _falhas[chave]
        return deque()
    return fila


def segundos_de_espera(email: str, ip: str) -> int:
    """0 se pode tentar. Senão, quantos segundos faltam para poder tentar de novo."""
    agora = _relogio()
    with _trava:
        espera = 0
        for chave, maximo in _chaves(email, ip):
            fila = _falhas_recentes(chave, agora)
            if len(fila) >= maximo:
                espera = max(espera, int(JANELA_SEGUNDOS - (agora - fila[0])) + 1)
        return espera


def registrar_falha(email: str, ip: str) -> None:
    agora = _relogio()
    with _trava:
        for chave, _ in _chaves(email, ip):
            _falhas.setdefault(chave, deque()).append(agora)


def limpar_email(email: str) -> None:
    """Chamado quando o login dá certo: zera as falhas desse e-mail."""
    with _trava:
        _falhas.pop(f"email:{email}", None)


def reiniciar() -> None:
    """Apaga tudo (usado nos testes)."""
    with _trava:
        _falhas.clear()