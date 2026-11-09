"""
Paradigma OOP — componentes do robô como entidades com identidade e estado.

ESQUELETO / PONTO DE PARTIDA. Preencher e adaptar. NÃO é código testado.
Ver ARQUITETURA.md, seção "Paradigma 1 — Orientação a Objetos".
"""

from dataclasses import dataclass, field
from enum import Enum


class EstadoRobo(Enum):
    OCIOSO = "ocioso"
    PATRULHANDO = "patrulhando"
    ATENDENDO = "atendendo"


class Prioridade(Enum):
    # valor maior = mais urgente
    PATRULHA = 0       # ronda de cuidado (qualquer chamado real a interrompe)
    PEDIDO_COMUM = 1   # ex.: água
    EMERGENCIA = 10    # ex.: queda


@dataclass
class Chamado:
    """Um chamado da pessoa assistida. Tem identidade (id) e prioridade."""
    id: str
    tipo: str                  # ex.: "queda", "agua"
    prioridade: Prioridade
    destino: tuple             # (x, y) na planta da casa


class Robo:
    """
    Entidade central com identidade e ESTADO MUTÁVEL — justamente o caso
    em que OOP é o paradigma adequado.
    """

    def __init__(self, nome: str):
        self.nome = nome
        self.estado = EstadoRobo.OCIOSO
        self.pose = (0.0, 0.0, 0.0)          # x, y, theta
        self.chamado_atual: Chamado | None = None

    def atualizar_pose(self, x: float, y: float, theta: float) -> None:
        self.pose = (x, y, theta)

    def iniciar_atendimento(self, chamado: Chamado) -> None:
        self.chamado_atual = chamado
        self.estado = EstadoRobo.ATENDENDO

    def concluir_atendimento(self) -> None:
        self.chamado_atual = None
        self.estado = EstadoRobo.PATRULHANDO
