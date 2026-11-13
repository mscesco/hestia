"""
Paradigma FUNCIONAL — pipeline de processamento de leituras de sensor como
cadeia de funções puras (sem estado compartilhado, sem efeito colateral).

USADO DE VERDADE: o nó `no_percepcao` (no_percepcao.py) assina o `/scan` do
LiDAR e passa cada varredura por `processar()`, publicando o resultado em
`/obstaculo_proximo`. Ou seja, este pipeline roda no sistema — não é ilustrativo.
Cada função abaixo é pura: mesma entrada -> mesma saída, testável isolada.

Ver ARQUITETURA.md, seção "Paradigma 2 — Funcional".
"""

from functools import reduce


# --- funções puras: entrada -> saída, sem tocar em estado externo ---

def filtrar_ruido(leitura: list[float]) -> list[float]:
    """Remove valores inválidos do LiDAR (inf, nan, negativos)."""
    return [v for v in leitura if v == v and v != float("inf") and v >= 0.0]


def normalizar(leitura: list[float], alcance_max: float = 16.0) -> list[float]:
    """Normaliza as distâncias para [0, 1] pelo alcance real do sensor.
    `alcance_max` casa com o laser do robô (16 m, ver ajustar_laser_16m.sh)."""
    if alcance_max <= 0:
        alcance_max = 1.0
    return [min(v / alcance_max, 1.0) for v in leitura]


def detectar_obstaculo_proximo(leitura_norm: list[float], limiar: float) -> bool:
    """Decisão final do pipeline: há algo perigosamente perto? (valores já
    normalizados em [0,1]; `limiar` também normalizado)."""
    return any(v < limiar for v in leitura_norm)


def processar(leitura_bruta: list[float],
              alcance_max: float = 16.0,
              distancia_perigo_m: float = 0.5) -> bool:
    """
    Compõe as etapas numa cadeia. Cada função é pura e testável isolada.
    Trocar/adicionar etapa = mudar a composição, sem tocar no resto.
    Retorna True se há obstáculo a menos de `distancia_perigo_m` metros.
    """
    limiar_norm = distancia_perigo_m / alcance_max
    etapas = [
        filtrar_ruido,
        lambda dado: normalizar(dado, alcance_max),
    ]
    processada = reduce(lambda dado, fn: fn(dado), etapas, leitura_bruta)
    return detectar_obstaculo_proximo(processada, limiar_norm)
