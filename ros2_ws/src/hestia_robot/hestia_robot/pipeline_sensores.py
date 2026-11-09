"""
Paradigma FUNCIONAL — pipeline de processamento de leituras de sensor
como cadeia de funções puras (sem estado compartilhado, sem efeito colateral).

ESQUELETO / PONTO DE PARTIDA. Preencher e adaptar. NÃO é código testado.
Ver ARQUITETURA.md, seção "Paradigma 2 — Funcional".
"""

from functools import reduce


# --- funções puras: entrada -> saída, sem tocar em estado externo ---

def filtrar_ruido(leitura: list[float]) -> list[float]:
    """Remove valores inválidos (ex.: infinito do LiDAR)."""
    return [v for v in leitura if v != float("inf")]


def normalizar(leitura: list[float]) -> list[float]:
    """Normaliza para [0, 1] assumindo alcance máximo de 10 m."""
    return [min(v / 10.0, 1.0) for v in leitura]


def detectar_obstaculo_proximo(leitura: list[float], limiar: float = 0.05) -> bool:
    """Decisão final do pipeline: há algo perigosamente perto?"""
    return any(v < limiar for v in leitura)


def processar(leitura_bruta: list[float]) -> bool:
    """
    Compõe as etapas numa cadeia. Cada função é pura e testável isolada.
    Trocar/adicionar etapa = mudar a composição, sem tocar no resto.
    """
    etapas = [filtrar_ruido, normalizar]
    processada = reduce(lambda dado, fn: fn(dado), etapas, leitura_bruta)
    return detectar_obstaculo_proximo(processada)
