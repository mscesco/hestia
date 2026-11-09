#!/usr/bin/env python3
"""
pose_tf_bridge.py — publica a pose VERDADEIRA do robô em /amcl_pose a partir da
TF `map -> base_footprint`.

Para que serve (PLANO B da demo): quando a localização não usa o AMCL e sim uma
TF estática `map -> odom` + a odometria (perfeita) do Gazebo, ninguém publica
/amcl_pose — e o `no_ponte` (que alimenta o Godot) assina justamente /amcl_pose.
Este nó preenche essa lacuna: lê a TF e republica a pose no mesmo tópico e tipo
(geometry_msgs/PoseWithCovarianceStamped), então `no_ponte` e o Godot funcionam
sem nenhuma alteração.

NÃO rode este nó junto com o AMCL (os dois publicariam /amcl_pose e brigariam).
É só para o fluxo sem AMCL (localizacao_blender_simples.launch.py).

Rodar (via launch do plano B, ou direto):
  python3 .../scripts/pose_tf_bridge.py --ros-args -p use_sim_time:=true
"""

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener


class PoseTfBridge(Node):
    def __init__(self):
        super().__init__("pose_tf_bridge")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("base_frame", "base_footprint")
        # tópico de saída: /pose_robo no plano B (evita conflito com o /amcl_pose
        # que o AMCL ainda publica). Default /amcl_pose por compatibilidade.
        self.declare_parameter("pose_topic", "/amcl_pose")
        self.map_frame = self.get_parameter("map_frame").value
        self.base_frame = self.get_parameter("base_frame").value
        pose_topic = self.get_parameter("pose_topic").value

        self.tf_buffer = Buffer()
        TransformListener(self.tf_buffer, self)
        self.pub = self.create_publisher(PoseWithCovarianceStamped, pose_topic, 10)
        self.create_timer(0.1, self._tick)   # 10 Hz
        self._avisou = False
        self.get_logger().info(
            f"pose_tf_bridge pronto — {self.map_frame}->{self.base_frame} -> {pose_topic}")

    def _tick(self):
        try:
            t = self.tf_buffer.lookup_transform(
                self.map_frame, self.base_frame, rclpy.time.Time())
        except Exception as e:
            if not self._avisou:
                self.get_logger().warn(f"ainda sem TF {self.map_frame}->{self.base_frame}: {e}")
                self._avisou = True
            return

        msg = PoseWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.map_frame
        msg.pose.pose.position.x = t.transform.translation.x
        msg.pose.pose.position.y = t.transform.translation.y
        msg.pose.pose.position.z = 0.0
        msg.pose.pose.orientation = t.transform.rotation
        # covariância pequena e fixa (localização de simulação = confiável)
        cov = [0.0] * 36
        cov[0] = cov[7] = 0.01     # x, y
        cov[35] = 0.01             # yaw
        msg.pose.covariance = cov
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = PoseTfBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
