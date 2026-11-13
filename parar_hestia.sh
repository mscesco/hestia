#!/bin/bash
# Derruba todos os processos do sistema Héstia no WSL.
# Uso: wsl -d Ubuntu-22.04 -u lauri bash /mnt/c/Users/lauri/Downloads/hestia/parar_hestia.sh
echo "[hestia] derrubando processos..."
pkill -9 -f "uvicorn servidor:app" 2>/dev/null
pkill -9 -f "ros2 launch hestia_robot" 2>/dev/null
pkill -9 -f gzserver 2>/dev/null
pkill -9 -f gzclient 2>/dev/null
pkill -9 -f rviz2 2>/dev/null
pkill -9 -f no_ponte 2>/dev/null
pkill -9 -f gerenciador_chamados 2>/dev/null
pkill -9 -f no_percepcao 2>/dev/null
pkill -9 -f pose_tf_bridge 2>/dev/null
pkill -9 -f explorador_nav2 2>/dev/null
pkill -9 -f nav2 2>/dev/null
# processos que faltavam: container de nós do Nav2, TF estática, gazebo,
# map_server e os lifecycle managers.
pkill -9 -f component_container 2>/dev/null
pkill -9 -f static_transform_publisher 2>/dev/null
pkill -9 -f gazebo 2>/dev/null
pkill -9 -f map_server 2>/dev/null
pkill -9 -f lifecycle_manager 2>/dev/null
pkill -9 -f robot_state_publisher 2>/dev/null
sleep 1
ros2 daemon stop 2>/dev/null   # limpa o cache de descoberta (some com nomes fantasmas)
echo "[hestia] feito."
