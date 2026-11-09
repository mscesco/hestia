#!/usr/bin/env python3
"""
localizacao_blender.launch.py — como o localizacao.launch.py, mas na CASA DO
BLENDER (casa_blender.world + mapa casa_blender.yaml), em vez da turtlebot3_house.

Sobe:
  1) gzserver (headless) com o mundo casa_blender.world (mesh exportado do
     .blend) — via ExecuteProcess, garantindo os plugins ros_init + ros_factory;
  2) robot_state_publisher do TB3 burger (TF do robô);
  3) spawn do burger DENTRO da casa, em (0, 6) (ponto livre verificado no mapa);
  4) Nav2 em modo localização (map_server servindo casa_blender.yaml + AMCL +
     planner/controller/bt_navigator), use_sim_time=true.

Não sobe RViz nem gzclient (demo roda headless; a visualização é o Godot).
O frame do Gazebo = frame do Blender, então o Godot alinha sem offset.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

_PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    mapa = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")

    pkg_tb3_gazebo = get_package_share_directory("turtlebot3_gazebo")
    pkg_nav2 = FindPackageShare("nav2_bringup")

    world = os.path.join(_PKG, "worlds", "casa_blender.world")

    args = [
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "map", default_value=os.path.join(_PKG, "maps", "casa_blender.yaml")),
        DeclareLaunchArgument(
            "params_file",
            default_value=os.path.join(_PKG, "config", "nav2_params.yaml")),
    ]

    # 1) Gazebo headless com a casa do Blender (plugins init+factory explicitos)
    gzserver = ExecuteProcess(
        cmd=["gzserver", "--verbose",
             "-s", "libgazebo_ros_init.so",
             "-s", "libgazebo_ros_factory.so",
             world],
        output="screen",
    )

    # 2) robot_state_publisher do TB3
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_tb3_gazebo, "launch", "robot_state_publisher.launch.py")),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    # 3) spawn do burger dentro da casa (0,6) — pequeno atraso p/ o gzserver subir
    spawn = TimerAction(period=4.0, actions=[
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_tb3_gazebo, "launch", "spawn_turtlebot3.launch.py")),
            launch_arguments={"x_pose": "0.0", "y_pose": "6.0"}.items(),
        )
    ])

    # 4) Nav2 em modo localização sobre o mapa da casa do Blender
    nav2 = TimerAction(period=6.0, actions=[
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([pkg_nav2, "launch", "bringup_launch.py"])),
            launch_arguments={
                "map": mapa,
                "use_sim_time": use_sim_time,
                "params_file": params_file,
            }.items(),
        )
    ])

    return LaunchDescription(args + [gzserver, rsp, spawn, nav2])
