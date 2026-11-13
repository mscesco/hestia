#!/usr/bin/env python3
"""
localizacao_blender_simples.launch.py — PLANO B da demo: casa do Blender com a
localização "cravada" da simulação, para GARANTIR a navegação lisa.

Estratégia (reusa o mesmo bringup do plano A, só troca a localização):
  - Sobe o Nav2 completo pelo `bringup_launch.py` (map_server + costmaps +
    planner/controller/bt), igual ao plano A — então o MAPA chega certo ao
    planejador (o que faltava na versão anterior do plano B);
  - usa `nav2_params_simples.yaml`, onde o AMCL está com `tf_broadcast: false`:
    ele roda mas NÃO controla a TF;
  - um `static_transform_publisher` publica `map -> odom` na pose de spawn (0,6).
    Como a odometria do Gazebo é exata, a posição do robô fica cravada e o Nav2
    navega liso (sem as recuperações/abortos do AMCL em casa aberta);
  - `pose_tf_bridge` lê a TF real (`map -> base_footprint`) e publica em
    `/pose_robo`; o `no_ponte` é apontado p/ esse tópico (ver iniciar_*.sh), para
    o Godot receber a pose EXATA (e não a estimativa do AMCL).

Honesto: é "trapaça de simulação" (não casa scan com mapa). É o seguro p/ a demo;
o fluxo com AMCL de verdade fica no localizacao_blender.launch.py.
"""

import os
import tempfile

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


def _gerar_world():
    """Gera um .world temporario com o caminho ABSOLUTO real do mesh desta
    maquina (substitui o token __OBJ_PATH__). Resolve o bug do caminho fixo:
    sem isto, em qualquer maquina diferente da do autor do .world o mesh nao
    carrega e a casa sobe VAZIA (sem paredes -> laser/AMCL/Nav2 quebram)."""
    template = os.path.join(_PKG, "worlds", "casa_blender.world")
    obj = os.path.join(_PKG, "worlds", "casa_blender", "casa_blender.obj")
    if not os.path.isfile(obj):
        raise FileNotFoundError(f"mesh da casa nao encontrado: {obj}")
    with open(template, "r", encoding="utf-8") as f:
        conteudo = f.read().replace("__OBJ_PATH__", obj)
    saida = os.path.join(tempfile.gettempdir(), "hestia_casa_blender.world")
    with open(saida, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return saida


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    mapa = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")

    pkg_tb3_gazebo = get_package_share_directory("turtlebot3_gazebo")
    pkg_nav2 = FindPackageShare("nav2_bringup")

    world = _gerar_world()
    bridge = os.path.join(_PKG, "scripts", "pose_tf_bridge.py")

    args = [
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "map", default_value=os.path.join(_PKG, "maps", "casa_blender.yaml")),
        DeclareLaunchArgument(
            "params_file",
            default_value=os.path.join(_PKG, "config", "nav2_params_simples.yaml")),
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

    # 4) TF estática map->odom na pose de spawn (0,6) — a localização "cravada".
    #    (O AMCL está com tf_broadcast:false no nav2_params_simples.yaml, então
    #    não há conflito de quem publica map->odom.)
    tf_map_odom = Node(
        package="tf2_ros", executable="static_transform_publisher", name="map_para_odom",
        arguments=["--x", "0.0", "--y", "6.0", "--z", "0.0",
                   "--yaw", "0.0", "--pitch", "0.0", "--roll", "0.0",
                   "--frame-id", "map", "--child-frame-id", "odom"],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    # 5) Nav2 COMPLETO pelo bringup (map_server + costmaps + planner/controller/bt
    #    + amcl SEM tf). Mesmo caminho do plano A -> o mapa chega ao planejador.
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

    # 6) ponte de pose: TF map->base_footprint -> /pose_robo (pose EXATA p/ Godot)
    pose_bridge = TimerAction(period=9.0, actions=[
        ExecuteProcess(
            cmd=["python3", bridge, "--ros-args",
                 "-p", "use_sim_time:=true",
                 "-p", "pose_topic:=/pose_robo"],
            output="screen",
        )
    ])

    # 7) RViz (opcional, ligado por padrão)
    rviz = TimerAction(period=10.0, actions=[
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
        args + [gzserver, rsp, spawn, tf_map_odom, nav2, pose_bridge, rviz])
