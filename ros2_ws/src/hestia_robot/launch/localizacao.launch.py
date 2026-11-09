#!/usr/bin/env python3
"""
localizacao.launch.py — SEMANA 3: navegação em malha fechada.

Sobe de uma vez:
  1) Gazebo com o mundo `turtlebot3_house`;
  2) Nav2 em modo LOCALIZAÇÃO — map_server servindo o `maps/casa.yaml` +
     AMCL (localização de Monte Carlo) + planner/controller/bt_navigator;
  3) RViz2 já configurado do Nav2 (para dar a pose inicial e enviar metas).

É a base do "malha fechada" que o professor exige: o robô NÃO executa às cegas,
ele se localiza continuamente no mapa salvo (AMCL) e o Nav2 replaneja.

--- COMO RODAR (sem precisar buildar o workspace) ---
  ros2 launch /mnt/c/Users/Usuario/Documents/hestia/ros2_ws/src/hestia_robot/launch/localizacao.launch.py

--- PRIMEIROS PASSOS NO RViz (importante) ---
  1) Clique em "2D Pose Estimate" e desenhe a seta na posição/direção onde o
     robô está no mapa (o AMCL precisa de um palpite inicial). A nuvem de setas
     (partículas) deve convergir ao redor do robô.
  2) Clique em "Nav2 Goal" e escolha um destino: o robô planeja e vai até lá,
     desviando de obstáculos. Isso valida a navegação antes da preempção.

use_sim_time=true é obrigatório (Gazebo publica /clock).
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

# Pasta do pacote (…/hestia_robot), resolvida a partir da posição deste arquivo.
_PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    mapa = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")

    pkg_tb3_gazebo = FindPackageShare("turtlebot3_gazebo")
    pkg_nav2 = FindPackageShare("nav2_bringup")

    args = [
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "map", default_value=os.path.join(_PKG, "maps", "casa.yaml"),
            description="Mapa salvo (.yaml) sobre o qual o AMCL se localiza.",
        ),
        DeclareLaunchArgument(
            "params_file",
            default_value=os.path.join(_PKG, "config", "nav2_params.yaml"),
            description="Parâmetros do Nav2 (AMCL, planner, controller, costmaps).",
        ),
    ]

    # 1) Gazebo + casa
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_tb3_gazebo, "launch", "turtlebot3_house.launch.py"])
        ),
    )

    # 2) Nav2 em modo localização (slam:=False -> usa map_server + AMCL)
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_nav2, "launch", "bringup_launch.py"])
        ),
        launch_arguments={
            "map": mapa,
            "use_sim_time": use_sim_time,
            "params_file": params_file,
        }.items(),
    )

    # 3) RViz2 com a visão padrão do Nav2 (tem os botões 2D Pose Estimate / Nav2 Goal)
    rviz_config = PathJoinSubstitution([pkg_nav2, "rviz", "nav2_default_view.rviz"])
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    return LaunchDescription(args + [gazebo, nav2, rviz])
