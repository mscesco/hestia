#!/usr/bin/env python3
"""
no_percepcao.py — nó ROS que EXECUTA o pipeline FUNCIONAL sobre o LiDAR.

É a prova de que o paradigma funcional (pipeline_sensores.py) roda no sistema, e
não só existe no papel: este nó assina `/scan` (sensor_msgs/LaserScan), passa a
varredura pela cadeia de funções puras `processar()` e publica o resultado
(booleano) em `/obstaculo_proximo` (std_msgs/Bool). O Nav2 continua cuidando do
desvio; este sinal é uma camada de percepção independente, fácil de demonstrar
("chegue perto do robô e o tópico vira True").

Rodar (após colcon build + source do install):
  ros2 run hestia_robot no_percepcao --ros-args -p use_sim_time:=true
Acompanhar:
  ros2 topic echo /obstaculo_proximo
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool

from hestia_robot.pipeline_sensores import processar


class NoPercepcao(Node):
    def __init__(self):
        super().__init__("no_percepcao")
        self.declare_parameter("alcance_max", 16.0)
        self.declare_parameter("distancia_perigo_m", 0.5)
        self._alcance = float(self.get_parameter("alcance_max").value)
        self._perigo = float(self.get_parameter("distancia_perigo_m").value)

        self.create_subscription(LaserScan, "/scan", self._on_scan, 10)
        self._pub = self.create_publisher(Bool, "/obstaculo_proximo", 10)
        self._ultimo = None
        self.get_logger().info(
            "no_percepcao pronto — /scan -> pipeline funcional -> /obstaculo_proximo")

    def _on_scan(self, msg: LaserScan) -> None:
        # entrada bruta do sensor -> cadeia de funções puras -> decisão
        perto = processar(list(msg.ranges),
                          alcance_max=self._alcance,
                          distancia_perigo_m=self._perigo)
        self._pub.publish(Bool(data=perto))
        if perto != self._ultimo:
            self._ultimo = perto
            self.get_logger().info(
                f"obstáculo próximo (<{self._perigo} m): {perto}")


def main():
    rclpy.init()
    node = NoPercepcao()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
