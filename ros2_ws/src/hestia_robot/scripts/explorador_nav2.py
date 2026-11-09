#!/usr/bin/env python3
"""
explorador_nav2.py — exploração autônoma por fronteiras usando o NAV2 (v4).

Como o explore_lite / robôs de limpeza: detecta as FRONTEIRAS (borda entre
conhecido e desconhecido) e manda o NAV2 dirigir até a melhor delas. O
planejador do Nav2 traça o caminho ótimo e o controlador dirige em velocidade
cheia — sem o "dirigir na reação" lento da versão anterior.

Ciclo: detecta fronteiras -> escolhe a de maior score (tamanho/dist) -> envia
como meta NavigateToPose -> ao concluir (ou timeout), escolhe a próxima. Fronteira
que falha/demora entra numa blacklist temporária. Acaba quando não há fronteiras.

Precisa do mapear.launch.py no ar (Gazebo + SLAM + Nav2).

Rodar:
  python3 .../scripts/explorador_nav2.py --ros-args -p use_sim_time:=true
"""

import math
import time

import numpy as np
import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Point
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from tf2_ros import Buffer, TransformListener
from visualization_msgs.msg import Marker, MarkerArray


class ExploradorNav2(Node):
    def __init__(self):
        super().__init__("explorador_nav2")
        mapa_qos = QoSProfile(depth=1, reliability=QoSReliabilityPolicy.RELIABLE,
                              durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(OccupancyGrid, "/map", self._on_map, mapa_qos)
        self.tf_buffer = Buffer()
        TransformListener(self.tf_buffer, self)
        self.nav = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self.marker_pub = self.create_publisher(MarkerArray, "/frontiers", 10)

        self.mapa = None
        self.ativo = False
        self.gh = None
        self.alvo = None
        self.t_envio = 0.0
        self.blacklist = []       # [(x, y, t)]
        self.vazio = 0

        self.create_timer(2.0, self._tick)
        self.get_logger().info("explorador_nav2 pronto — Nav2 dirige até as fronteiras.")

    def _on_map(self, msg):
        self.mapa = msg

    def _pose(self):
        try:
            t = self.tf_buffer.lookup_transform("map", "base_footprint", rclpy.time.Time())
        except Exception:
            return None
        return (t.transform.translation.x, t.transform.translation.y)

    def _fronteiras(self, pose):
        m = self.mapa
        w, h, res = m.info.width, m.info.height, m.info.resolution
        ox, oy = m.info.origin.position.x, m.info.origin.position.y
        d = np.array(m.data, dtype=np.int16).reshape(h, w)
        free = (d >= 0) & (d <= 25)
        unk = d < 0
        nb = np.zeros((h, w), dtype=bool)
        nb[:, :-1] |= unk[:, 1:]
        nb[:, 1:] |= unk[:, :-1]
        nb[:-1, :] |= unk[1:, :]
        nb[1:, :] |= unk[:-1, :]
        ys, xs = np.where(free & nb)
        if len(xs) == 0:
            return [], 0
        wx = ox + (xs + 0.5) * res
        wy = oy + (ys + 0.5) * res

        bins = {}
        for x, y in zip(wx, wy):
            k = (round(x / 0.5), round(y / 0.5))
            b = bins.get(k)
            if b is None:
                bins[k] = [1, x, y]
            else:
                b[0] += 1; b[1] += x; b[2] += y

        agora = time.time()
        self.blacklist = [bl for bl in self.blacklist if agora - bl[2] < 25.0]
        cands = []
        for n, sx, sy in bins.values():
            if n < 3:
                continue
            cx, cy = sx / n, sy / n
            dist = math.hypot(cx - pose[0], cy - pose[1])
            if dist < 0.5:      # fronteira colada no robô = beco sem saída, ignora
                continue
            if any(math.hypot(cx - bx, cy - by) < 0.8 for bx, by, _ in self.blacklist):
                continue
            cands.append((n / (dist + 1.0), dist, cx, cy))
        cands.sort(reverse=True)
        return cands, len(xs)

    def _publicar_marcadores(self, cands):
        """Mostra as fronteiras (azul) e o alvo atual (verde) no RViz (/frontiers)."""
        arr = MarkerArray()
        limpa = Marker()
        limpa.action = Marker.DELETEALL
        arr.markers.append(limpa)

        pts = Marker()
        pts.header.frame_id = "map"
        pts.header.stamp = self.get_clock().now().to_msg()
        pts.ns = "fronteiras"
        pts.id = 1
        pts.type = Marker.SPHERE_LIST
        pts.action = Marker.ADD
        pts.scale.x = pts.scale.y = pts.scale.z = 0.15
        pts.color.b = 1.0
        pts.color.g = 0.4
        pts.color.a = 0.8
        for _, _, cx, cy in cands:
            pts.points.append(Point(x=float(cx), y=float(cy), z=0.1))
        arr.markers.append(pts)

        if self.alvo is not None:
            tgt = Marker()
            tgt.header.frame_id = "map"
            tgt.header.stamp = pts.header.stamp
            tgt.ns = "alvo"
            tgt.id = 2
            tgt.type = Marker.SPHERE
            tgt.action = Marker.ADD
            tgt.pose.position.x = float(self.alvo[0])
            tgt.pose.position.y = float(self.alvo[1])
            tgt.pose.position.z = 0.15
            tgt.pose.orientation.w = 1.0
            tgt.scale.x = tgt.scale.y = tgt.scale.z = 0.35
            tgt.color.g = 1.0
            tgt.color.r = 0.1
            tgt.color.a = 0.9
            arr.markers.append(tgt)
        self.marker_pub.publish(arr)

    def _tick(self):
        if self.mapa is None:
            return
        pose = self._pose()
        if pose is None:
            return

        cands, n_cells = self._fronteiras(pose)
        self._publicar_marcadores(cands)   # fronteiras + alvo no RViz (topico /frontiers)

        if self.ativo:
            if time.time() - self.t_envio > 25.0:
                self.get_logger().warn("meta demorou demais — cancelando e trocando.")
                if self.gh is not None:
                    self.gh.cancel_goal_async()
                if self.alvo:
                    self.blacklist.append((self.alvo[0], self.alvo[1], time.time()))
                self.ativo = False
                self.gh = None
            return

        if not cands:
            if n_cells == 0:
                self.vazio += 1
                self.get_logger().info(f"sem fronteiras ({self.vazio}/3)")
                if self.vazio >= 3:
                    self.get_logger().info(">>> EXPLORACAO COMPLETA.")
            else:
                self.get_logger().info(
                    f"fronteiras em cooldown/perto demais ({n_cells} cels) — aguardando")
            return
        self.vazio = 0
        _, dist, cx, cy = cands[0]
        self._enviar((cx, cy), dist, len(cands))

    def _enviar(self, alvo, dist, ncand):
        if not self.nav.wait_for_server(timeout_sec=3.0):
            self.get_logger().error("Nav2 (navigate_to_pose) indisponível.")
            return
        g = NavigateToPose.Goal()
        g.pose.header.frame_id = "map"
        g.pose.header.stamp = self.get_clock().now().to_msg()
        g.pose.pose.position.x = float(alvo[0])
        g.pose.pose.position.y = float(alvo[1])
        g.pose.pose.orientation.w = 1.0
        self.ativo = True
        self.alvo = alvo
        self.t_envio = time.time()
        # blacklista o alvo ao enviar: evita fixar na mesma fronteira, força rodar
        self.blacklist.append((alvo[0], alvo[1], time.time()))
        self.get_logger().info(
            f"-> Nav2: fronteira ({alvo[0]:.2f},{alvo[1]:.2f}) dist={dist:.2f} cands={ncand}")
        self.nav.send_goal_async(g).add_done_callback(self._aceita)

    def _aceita(self, fut):
        gh = fut.result()
        if not gh.accepted:
            self.get_logger().warn("Nav2 rejeitou a meta — blacklist.")
            if self.alvo:
                self.blacklist.append((self.alvo[0], self.alvo[1], time.time()))
            self.ativo = False
            return
        self.gh = gh
        gh.get_result_async().add_done_callback(self._resultado)

    def _resultado(self, fut):
        status = fut.result().status
        if status != GoalStatus.STATUS_SUCCEEDED and self.alvo:
            # não chegou: evita re-tentar a mesma fronteira por um tempo
            self.blacklist.append((self.alvo[0], self.alvo[1], time.time()))
        self.ativo = False
        self.gh = None


def main():
    rclpy.init()
    node = ExploradorNav2()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
