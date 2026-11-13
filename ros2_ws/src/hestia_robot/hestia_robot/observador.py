"""
Padrão de Projeto OBSERVER (GoF) — implementação AUTORAL explícita.

Por que este arquivo existe: dizer apenas "os tópicos do ROS 2 já são pub/sub,
logo é Observer" é fraco numa arguição ("isso é o ROS, não VOCÊS aplicando o
padrão"). Aqui o padrão é implementado de fato: um `Sujeito` mantém uma lista de
`Observador`es, e ao mudar de estado chama `notificar()` — cada observador reage
sem que o sujeito saiba quem são nem o que fazem.

Onde é usado: `gerenciador_chamados` é um `Sujeito`. Quando a atividade do robô
muda (ronda / atendendo queda / ocioso), ele notifica dois observadores:
  - `LogAtividade`         — registra no logger do nó;
  - `PublicadorAtividade`  — publica em /atividade_robo (ponte -> Godot).
Adicionar um novo reação (ex.: acender um LED, gravar métrica) = criar outro
Observador e inscrevê-lo, SEM tocar no sujeito. É esse desacoplamento que o
padrão entrega.
"""

from abc import ABC, abstractmethod


class Observador(ABC):
    """Interface do observador: reage a uma notificação do sujeito."""

    @abstractmethod
    def atualizar(self, evento: str) -> None:
        ...


class Sujeito:
    """Mantém observadores e os notifica. Não conhece as classes concretas."""

    def __init__(self) -> None:
        self._observadores: list[Observador] = []

    def inscrever(self, obs: Observador) -> None:
        if obs not in self._observadores:
            self._observadores.append(obs)

    def desinscrever(self, obs: Observador) -> None:
        if obs in self._observadores:
            self._observadores.remove(obs)

    def notificar(self, evento: str) -> None:
        for obs in self._observadores:
            obs.atualizar(evento)


class LogAtividade(Observador):
    """Observador concreto: escreve a atividade no logger do nó ROS."""

    def __init__(self, logger) -> None:
        self._logger = logger

    def atualizar(self, evento: str) -> None:
        self._logger.info(f"[atividade] {evento}")


class PublicadorAtividade(Observador):
    """Observador concreto: publica a atividade em /atividade_robo (String).
    Recebe o publisher já criado pelo nó — não conhece o ROS além disso."""

    def __init__(self, publisher, String) -> None:
        self._pub = publisher
        self._String = String

    def atualizar(self, evento: str) -> None:
        self._pub.publish(self._String(data=evento))
