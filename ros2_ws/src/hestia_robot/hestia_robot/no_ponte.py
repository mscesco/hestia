"""
no_ponte.py — assina a pose do robô (AMCL) e publica na ponte FastAPI (HTTP).

Assina `/amcl_pose` (geometry_msgs/PoseWithCovarianceStamped, publicado pelo
AMCL) e faz `POST /pose` no servidor-ponte a cada atualização, convertendo o
quatérnio de orientação para o ângulo `theta` (yaw) que o Godot consome.

Parâmetros ROS (podem ser passados por --ros-args -p):
  ponte_host (default: "localhost")
  ponte_porta (default: 8000)

Rodar (após `colcon build` + source do install):
  ros2 run hestia_robot no_ponte
Precisa do AMCL no ar (localizacao.launch.py) e da ponte rodando
(`uvicorn servidor:app` em ../../ponte).

Câmera "pelos olhos do robô": resolvida no Godot (painel picture-in-picture,
SubViewport espelhando a câmera do robô) — não trafega pela rede, então este nó
não envia imagem. Um /stream HTTP (MJPEG da câmera real do Gazebo) fica como
evolução futura, fora do escopo atual.
"""

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
        host = self.get_parameter("ponte_host").value
        porta = self.get_parameter("ponte_porta").value
        self._url_pose = f"http://{host}:{porta}/pose"
        self._url_atividade = f"http://{host}:{porta}/atividade"

        self.create_subscription(
            PoseWithCovarianceStamped, "/amcl_pose", self._on_pose, 10)
        # atividade do robô (ronda / atendendo queda) -> ponte -> Godot
        self.create_subscription(String, "/atividade_robo", self._on_atividade, 10)

        self.get_logger().info(
            f"no_ponte pronto — assinando /amcl_pose + /atividade_robo, "
            f"publicando em {self._url_pose}")

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
