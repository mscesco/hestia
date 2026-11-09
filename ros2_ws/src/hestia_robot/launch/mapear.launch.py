#!/usr/bin/env python3
"""
mapear.launch.py — MAPEAMENTO AUTÔNOMO "de robô aspirador" (Semana 2, v5).

Pipeline do professor, com SLAM em modo ASSÍNCRONO (estável):
  1) Gazebo com `turtlebot3_house` (robô nasce DENTRO, em -3.96, 1.02);
  2) slam_toolbox em modo ONLINE ASYNC (publica /map + TF map->odom ao vivo);
  3) Nav2 SÓ a navegação (planner/controller/costmaps) — consome o /map do SLAM;
  4) RViz2.

Por que async e não o sync do nav2_bringup: o sync processa os scans em série e
TRAVA sob carga (foi o que aconteceu). O async processa numa thread separada e
descarta scan atrasado em vez de travar — é o recomendado para exploração.

Rodar:
  ros2 launch /mnt/c/Users/Usuario/Documents/hestia/ros2_ws/src/hestia_robot/launch/mapear.launch.py

Depois (Claude): python3 .../scripts/explorador_nav2.py --ros-args -p use_sim_time:=true
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

_PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    params_file = LaunchConfiguration("params_file")

    pkg_tb3 = FindPackageShare("turtlebot3_gazebo")
    pkg_nav2 = FindPackageShare("nav2_bringup")
    pkg_slam = FindPackageShare("slam_toolbox")

    args = [
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "params_file",
            default_value=os.path.join(_PKG, "config", "nav2_exploracao.yaml")),
    ]

    # 1) Gazebo + casa, robô nascendo DENTRO
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_tb3, "launch", "turtlebot3_house.launch.py"])),
        launch_arguments={"x_pose": "-3.96", "y_pose": "1.02"}.items(),
    )

    # 2) SLAM ASSÍNCRONO (estável sob carga)
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_slam, "launch", "online_async_launch.py"])),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    # 3) Nav2 SÓ navegação (sem slam/localization próprios; usa o /map do slam_toolbox)
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_nav2, "launch", "navigation_launch.py"])),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": params_file,
        }.items(),
    )

    rviz_config = PathJoinSubstitution([pkg_nav2, "rviz", "nav2_default_view.rviz"])
    rviz = Node(
        package="rviz2", executable="rviz2", name="rviz2",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    return LaunchDescription(args + [gazebo, slam, nav2, rviz])
