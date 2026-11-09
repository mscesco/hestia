#!/usr/bin/env python3
"""
localizacao_blender_simples.launch.py — PLANO B da demo: casa do Blender SEM
AMCL. Em vez de localizar casando o laser com o mapa (AMCL, que ainda diverge em
áreas abertas desta casa), usa uma TF ESTÁTICA `map -> odom` e confia na
odometria (perfeita) do Gazebo. Localização de simulação "cravada" — o robô
navega liso e o Godot mostra a pose certa, sem depender do AMCL convergir.

Sobe:
  1) gzserver (headless) com casa_blender.world (plugins init + factory);
  2) robot_state_publisher do TB3 burger;
  3) spawn do burger em (0, 6);
  4) TF estática map->odom em (0, 6) (= pose de spawn; frame do Gazebo = frame
     do mapa, então isto alinha o robô no mapa);
  5) map_server servindo casa_blender.yaml (para o custo global do Nav2) +
     lifecycle_manager que o ativa;
  6) Nav2 SÓ navegação (planner/controller/bt/costmaps) — navigation_launch.py,
     SEM amcl e SEM map_server próprio;
  7) pose_tf_bridge: publica a pose real (TF map->base_footprint) em /amcl_pose,
     para o no_ponte/Godot continuarem funcionando sem alteração;
  8) RViz (opcional, arg `rviz`, ligado por padrão).

Trade-off honesto: esta localização é "trapaça de simulação" (não casa scan com
mapa como o AMCL). É o seguro para GARANTIR a demo; o fluxo com AMCL fica no
localizacao_blender.launch.py.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess,
                            IncludeLaunchDescription, TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

_PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    mapa = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")

    pkg_tb3_gazebo = get_package_share_directory("turtlebot3_gazebo")
    pkg_nav2 = FindPackageShare("nav2_bringup")

    world = os.path.join(_PKG, "worlds", "casa_blender.world")
    bridge = os.path.join(_PKG, "scripts", "pose_tf_bridge.py")

    args = [
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "map", default_value=os.path.join(_PKG, "maps", "casa_blender.yaml")),
        DeclareLaunchArgument(
            "params_file",
            default_value=os.path.join(_PKG, "config", "nav2_params.yaml")),
        DeclareLaunchArgument("rviz", default_value="true"),
    ]

    # 1) Gazebo headless com a casa do Blender
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

    # 3) spawn do burger dentro da casa (0,6)
    spawn = TimerAction(period=4.0, actions=[
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_tb3_gazebo, "launch", "spawn_turtlebot3.launch.py")),
            launch_arguments={"x_pose": "0.0", "y_pose": "6.0"}.items(),
        )
    ])

    # 4) TF estática map->odom na pose de spawn (0,6), sem rotação
    tf_map_odom = Node(
        package="tf2_ros", executable="static_transform_publisher", name="map_para_odom",
        arguments=["--x", "0.0", "--y", "6.0", "--z", "0.0",
                   "--yaw", "0.0", "--pitch", "0.0", "--roll", "0.0",
                   "--frame-id", "map", "--child-frame-id", "odom"],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    # 5) map_server + lifecycle_manager que o ativa (para o custo global do Nav2)
    mapa_stack = TimerAction(period=5.0, actions=[
        Node(
            package="nav2_map_server", executable="map_server", name="map_server",
            output="screen",
            parameters=[{"yaml_filename": mapa, "use_sim_time": use_sim_time,
                         "topic_name": "map", "frame_id": "map"}],
        ),
        Node(
            package="nav2_lifecycle_manager", executable="lifecycle_manager",
            name="lifecycle_manager_localization", output="screen",
            parameters=[{"use_sim_time": use_sim_time, "autostart": True,
                         "node_names": ["map_server"]}],
        ),
    ])

    # 6) Nav2 SÓ navegação (sem amcl, sem map_server próprio)
    nav2 = TimerAction(period=7.0, actions=[
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([pkg_nav2, "launch", "navigation_launch.py"])),
            launch_arguments={
                "use_sim_time": use_sim_time,
                "params_file": params_file,
            }.items(),
        )
    ])

    # 7) ponte de pose: TF map->base_footprint -> /amcl_pose (para no_ponte/Godot)
    pose_bridge = TimerAction(period=8.0, actions=[
        ExecuteProcess(
            cmd=["python3", bridge, "--ros-args", "-p", "use_sim_time:=true"],
            output="screen",
        )
    ])

    # 8) RViz (opcional, ligado por padrão)
    rviz = TimerAction(period=9.0, actions=[
        Node(
            package="rviz2", executable="rviz2", name="rviz2",
            arguments=["-d", PathJoinSubstitution(
                [pkg_nav2, "rviz", "nav2_default_view.rviz"])],
            parameters=[{"use_sim_time": use_sim_time}],
            output="screen",
            condition=IfCondition(LaunchConfiguration("rviz")),
        )
    ])

    return LaunchDescription(
        args + [gzserver, rsp, spawn, tf_map_odom, mapa_stack, nav2, pose_bridge, rviz])
