#!/usr/bin/env python3
"""
gerenciador_chamados.py — fila de prioridade + PREEMPÇÃO de metas do Nav2.

O CORAÇÃO da robótica do Héstia e o ponto que o professor exige explicitamente:
ao chegar um chamado de MAIOR prioridade (queda) enquanto o robô atende um de
MENOR (água), a meta de navegação atual do Nav2 é CANCELADA (preemptada) e a
nova é enviada — não é um `if`, é a API de ações (cancel_goal_async + novo
send_goal_async).

PADRÃO OBSERVER: este nó se INSCREVE no tópico `/chamados`. Quem publica o
chamado não sabe que este gerenciador existe (pub/sub do ROS 2 = Observer).

TRANSPORTE DO CHAMADO: `std_msgs/String` com JSON (decisão de arquitetura —
evita compilar um pacote de .msg custom em ament_python). Formato:
  {"tipo":"queda", "prioridade":"EMERGENCIA", "x":-5.0, "y":2.5}

RONDA: quando não há chamado, o robô patrulha waypoints (prioridade PATRULHA=0),
então QUALQUER chamado real a interrompe pela MESMA lógica de preempção.

Rodar (após `colcon build` + source do install):
  ros2 run hestia_robot gerenciador_chamados
Ou direto pelo caminho (usa o shim de sys.path abaixo):
  python3 .../hestia_robot/gerenciador_chamados.py --ros-args -p use_sim_time:=true

Precisa do Nav2 no ar (localizacao_blender.launch.py ou
localizacao_blender_simples.launch.py) — normalmente subido pelos scripts
iniciar_hestia_blender*.sh, que já iniciam este nó.
"""

import heapq
import itertools
import json
import os
import sys

# permite rodar tanto por `ros2 run` (buildado) quanto direto pelo caminho
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rclpy
from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import String

from hestia_robot.modelos import Chamado, Prioridade

# Waypoints da ronda de cuidado (pontos alcançáveis verificados no mapa).
# Poderiam vir de config/waypoints.yaml; inline por simplicidade.
# Ajustados para a CASA DO BLENDER (casa_blender.world + casa_blender.pgm,
# 2026-11): os 4 pontos passam pelos 4 cômodos (Sala, Quarto, Cozinha,
# Banheiro), extraídos do espaço livre do mapa com folga de parede, todos
# alcançáveis a partir do spawn (0,6). (Os pontos antigos eram da casa do TB3.)
RONDA = [(-7.9, -1.8), (-7.9, 11.45), (5.85, 9.7), (5.0, -1.9)]


class GerenciadorChamados(Node):
    """OBSERVER + fila de prioridade + preempção de metas do Nav2."""

    def __init__(self):
        super().__init__("gerenciador_chamados")

        self._fila = []                 # heap de (-prioridade, seq, Chamado)
        self._seq = itertools.count()   # desempate estável (FIFO dentro da prioridade)
        self._ativo = None              # Chamado em atendimento
        self._goal_handle = None        # handle da meta Nav2 em curso
        self._preemptar = False         # sinaliza que o cancelamento é preempção
        self._ronda_i = 0               # índice da ronda

        self._nav = ActionClient(self, NavigateToPose, "navigate_to_pose")

        # OBSERVER: inscrição no tópico de chamados
        self.create_subscription(String, "/chamados", self._on_chamado, 10)

        # publica a atividade atual do robô (/atividade_robo). A ponte repassa
        # ao Godot, que usa isso para acender o realce de emergência.
        self._pub_atividade = self.create_publisher(String, "/atividade_robo", 10)
        self._ultima_atividade = None

        # timer que injeta a ronda quando o robô está ocioso
        self.create_timer(1.0, self._talvez_rondar)

        self.get_logger().info("gerenciador_chamados pronto — aguardando /chamados.")

    # ---------- OBSERVER: chega um chamado ----------
    def _on_chamado(self, msg: String) -> None:
        try:
            d = json.loads(msg.data)
            prio = d.get("prioridade", "PEDIDO_COMUM")
            prioridade = Prioridade[prio] if isinstance(prio, str) else Prioridade(int(prio))
            ch = Chamado(
                id=str(d.get("id", next(self._seq))),
                tipo=str(d["tipo"]),
                prioridade=prioridade,
                destino=(float(d["x"]), float(d["y"])),
            )
        except Exception as e:
            self.get_logger().error(f"chamado inválido: {msg.data!r} ({e})")
            return

        self.get_logger().info(
            f"CHAMADO: {ch.tipo} [{ch.prioridade.name}] -> {ch.destino}")
        heapq.heappush(self._fila, (-ch.prioridade.value, next(self._seq), ch))
        self._avaliar()

    # ---------- decisão de preempção ----------
    def _avaliar(self) -> None:
        if self._ativo is None:
            self._despachar_proximo()
            return
        # há algo ativo: o topo da fila é MAIS urgente que o atendimento atual?
        if self._fila and self._fila[0][2].prioridade.value > self._ativo.prioridade.value:
            novo = self._fila[0][2]
            self.get_logger().warn(
                f"PREEMPCAO: {novo.tipo}[{novo.prioridade.name}] interrompe "
                f"{self._ativo.tipo}[{self._ativo.prioridade.name}] — cancelando meta Nav2")
            self._preemptar = True
            if self._goal_handle is not None:
                self._goal_handle.cancel_goal_async()
            # o restante acontece em _meta_resultado quando o cancelamento efetiva

    # ---------- ronda quando ocioso ----------
    def _talvez_rondar(self) -> None:
        if self._ativo is None and not self._fila:
            destino = RONDA[self._ronda_i % len(RONDA)]
            self._ronda_i += 1
            ronda = Chamado(id=f"ronda-{self._ronda_i}", tipo="ronda",
                            prioridade=Prioridade.PATRULHA, destino=destino)
            heapq.heappush(self._fila, (-ronda.prioridade.value, next(self._seq), ronda))
            self._despachar_proximo()

    # ---------- despacho / envio de meta ----------
    def _despachar_proximo(self) -> None:
        if self._ativo is not None or not self._fila:
            return
        _, _, ch = heapq.heappop(self._fila)
        self._ativo = ch
        self._enviar_meta(ch)

    def _enviar_meta(self, ch: Chamado) -> None:
        if not self._nav.wait_for_server(timeout_sec=3.0):
            self.get_logger().error("Nav2 (navigate_to_pose) indisponível.")
            self._ativo = None
            return
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = "map"
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = float(ch.destino[0])
        goal.pose.pose.position.y = float(ch.destino[1])
        goal.pose.pose.orientation.w = 1.0
        self.get_logger().info(f"-> Nav2: {ch.tipo} rumo a {ch.destino}")
        self._publicar_atividade(ch)
        self._nav.send_goal_async(goal).add_done_callback(self._meta_aceita)

    def _publicar_atividade(self, ch) -> None:
        """Publica a atividade atual em /atividade_robo (ronda / atendendo X /
        ocioso). A ponte repassa ao Godot, que acende o realce na emergência."""
        if ch is None:
            texto = "ocioso"
        elif ch.prioridade == Prioridade.PATRULHA:
            texto = "ronda"
        else:
            texto = f"atendendo {ch.tipo}"
        if texto != self._ultima_atividade:
            self._ultima_atividade = texto
            self._pub_atividade.publish(String(data=texto))

    def _meta_aceita(self, fut) -> None:
        gh = fut.result()
        if not gh.accepted:
            self.get_logger().error("Nav2 rejeitou a meta.")
            self._ativo = None
            self._despachar_proximo()
            return
        self._goal_handle = gh
        gh.get_result_async().add_done_callback(self._meta_resultado)

    def _meta_resultado(self, fut) -> None:
        """Único ponto de término de meta (sucesso, aborto OU cancelamento)."""
        status = fut.result().status
        antigo = self._ativo
        self._ativo = None
        self._goal_handle = None

        if self._preemptar:
            self._preemptar = False
            if antigo is not None and antigo.prioridade != Prioridade.PATRULHA:
                # re-enfileira o chamado interrompido para retomar depois da emergência
                heapq.heappush(self._fila, (-antigo.prioridade.value, next(self._seq), antigo))
                self.get_logger().info(f"{antigo.tipo} re-enfileirado (retoma após a emergência).")
        elif status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f"CONCLUIDO: {antigo.tipo if antigo else '?'}")
        else:
            self.get_logger().warn(f"meta terminou com status={status}")

        self._despachar_proximo()


def main():
    rclpy.init()
    node = GerenciadorChamados()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
