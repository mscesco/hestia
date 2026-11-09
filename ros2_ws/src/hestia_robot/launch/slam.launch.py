#!/usr/bin/env python3
"""
slam.launch.py — SEMANA 2: mapeamento da casa com slam_toolbox.

Sobe TRÊS coisas de uma vez só:
  1) Gazebo com o mundo `turtlebot3_house` (o robô que você vai dirigir);
  2) slam_toolbox (modo online async) construindo o mapa em tempo real;
  3) RViz2 para você VER o mapa sendo desenhado enquanto dirige.

Depois, em OUTRO terminal, você dirige o robô (teleop) e salva o mapa.
Passo a passo completo no launch/README.md e maps/README.md.

--- COMO RODAR ---
Sem precisar buildar o workspace (roda direto pelo caminho do arquivo):

  ros2 launch /mnt/c/Users/Usuario/Documents/hestia/ros2_ws/src/hestia_robot/launch/slam.launch.py

Mais tarde, com o workspace buildado (Semana 3), também funciona por pacote:

  ros2 launch hestia_robot slam.launch.py

use_sim_time=true é OBRIGATÓRIO aqui: o Gazebo publica o relógio da simulação
em /clock, e o SLAM precisa usar esse relógio (não o do computador) para casar
as leituras do LiDAR com a posição do robô no tempo certo.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")

    pkg_tb3_gazebo = FindPackageShare("turtlebot3_gazebo")
    pkg_slam = FindPackageShare("slam_toolbox")
    pkg_tb3_carto = FindPackageShare("turtlebot3_cartographer")

    declarar_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Usar o relógio da simulação (Gazebo publica /clock).",
    )

    # 1) Gazebo + mundo da casa (mesmo launch do portão de saída da Semana 1)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [pkg_tb3_gazebo, "launch", "turtlebot3_house.launch.py"]
            )
        ),
    )

    # 2) slam_toolbox em modo online assíncrono, desenhando o /map ao vivo
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [pkg_slam, "launch", "online_async_launch.py"]
            )
        ),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    # 3) RViz2 já configurado (mapa + leituras do LiDAR + TF).
    #    Reaproveitamos a config do turtlebot3_cartographer — os displays
    #    (Map em /map, LaserScan em /scan, TF) servem igual para o slam_toolbox.
    #    Na Semana 3 você pode salvar a sua própria config em rviz/.
    rviz_config = PathJoinSubstitution(
        [pkg_tb3_carto, "rviz", "tb3_cartographer.rviz"]
    )
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    return LaunchDescription([declarar_use_sim_time, gazebo, slam, rviz])
