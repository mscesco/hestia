"""
no_ponte.py — ponte de mão dupla entre ROS 2 e a ponte FastAPI (HTTP).

Saída (ROS -> HTTP): assina `/amcl_pose` (geometry_msgs/PoseWithCovarianceStamped,
publicado pelo AMCL) e faz `POST /pose` no servidor a cada atualização,
convertendo o quatérnio de orientação para o ângulo `theta` (yaw) que o Godot
consome. Também repassa a atividade (`/atividade_robo` -> `POST /atividade`).

Entrada (HTTP -> ROS): a cada 0,5 s drena `GET /pedidos` (pedidos feitos pela
interface Godot, autenticada) e republica cada um em `/chamados`
(std_msgs/String com JSON) — onde o gerenciador_chamados aplica a prioridade e a
preempção. É assim que um clique na UI vira uma meta de navegação.

Parâmetros ROS (podem ser passados por --ros-args -p):
  ponte_host (default: "localhost")
  ponte_porta (default: 8000)

Rodar (após `colcon build` + source do install):
  ros2 run hestia_robot no_ponte
Precisa do Nav2/pose no ar (localizacao_blender*.launch.py) e da ponte rodando
(`uvicorn servidor:app` em ../../ponte).

Câmera "pelos olhos do robô": resolvida no Godot (painel picture-in-picture,
SubViewport espelhando a câmera do robô) — não trafega pela rede, então este nó
não envia imagem. Um /stream HTTP (MJPEG da câmera real do Gazebo) fica como
evolução futura, fora do escopo atual.
"""

import json
import math

import requests
import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node
from std_msgs.msg import String


def _yaw_do_quaternio(q) -> float:
    """Extrai o ângulo yaw (rotação no plano, em radianos) de um quatérnio.
    Fórmula padrão (ver REP 103 / convenção ROS): só nos importa a rotação em
    torno de Z, já que o robô se move no plano."""
    seno = 2.0 * (q.w * q.z + q.x * q.y)
    coseno = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(seno, coseno)


class NoPonte(Node):
    def __init__(self):
        super().__init__("no_ponte")

        self.declare_parameter("ponte_host", "localhost")
        self.declare_parameter("ponte_porta", 8000)
        # tópico da pose: /amcl_pose (plano A) ou /pose_robo (plano B, via
        # pose_tf_bridge — pose exata da TF). Configurável p/ não duplicar o nó.
        self.declare_parameter("pose_topic", "/amcl_pose")
        host = self.get_parameter("ponte_host").value
        porta = self.get_parameter("ponte_porta").value
        pose_topic = self.get_parameter("pose_topic").value
        self._url_pose = f"http://{host}:{porta}/pose"
        self._url_atividade = f"http://{host}:{porta}/atividade"
        self._url_pedidos = f"http://{host}:{porta}/pedidos"

        self.create_subscription(
            PoseWithCovarianceStamped, pose_topic, self._on_pose, 10)
        # atividade do robô (ronda / atendendo queda) -> ponte -> Godot
        self.create_subscription(String, "/atividade_robo", self._on_atividade, 10)

        # ENTRADA: pedidos da interface (HTTP) -> tópico /chamados (ROS)
        self._pub_chamados = self.create_publisher(String, "/chamados", 10)
        self.create_timer(0.5, self._drenar_pedidos)

        self.get_logger().info(
            f"no_ponte pronto — assinando {pose_topic} + /atividade_robo, "
            f"publicando em {self._url_pose} e drenando pedidos de {self._url_pedidos}")

    def _on_pose(self, msg: PoseWithCovarianceStamped) -> None:
        p = msg.pose.pose.position
        theta = _yaw_do_quaternio(msg.pose.pose.orientation)
        try:
            requests.post(
                self._url_pose,
                params={"x": p.x, "y": p.y, "theta": theta},
                timeout=1.0,
            )
        except requests.exceptions.RequestException as e:
            # a ponte pode ainda não estar no ar — não derruba o nó por isso
            self.get_logger().warn(f"falha ao publicar pose na ponte: {e}")

    def _on_atividade(self, msg: String) -> None:
        try:
            requests.post(
                self._url_atividade, params={"texto": msg.data}, timeout=1.0)
        except requests.exceptions.RequestException:
            pass  # telemetria best-effort; não derruba o nó

    def _drenar_pedidos(self) -> None:
        """Puxa os pedidos enfileirados pela interface e publica em /chamados."""
        try:
            r = requests.get(self._url_pedidos, timeout=1.0)
        except requests.exceptions.RequestException:
            return  # ponte pode não estar no ar ainda; tenta de novo no próximo tick
        if r.status_code != 200:
            return
        for p in r.json().get("pedidos", []):
            msg = String(data=json.dumps(p))
            self._pub_chamados.publish(msg)
            self.get_logger().info(f"pedido da interface -> /chamados: {p}")


def main():
    rclpy.init()
    node = NoPonte()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
