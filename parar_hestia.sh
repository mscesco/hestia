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
pkill -9 -f pose_tf_bridge 2>/dev/null
pkill -9 -f explorador_nav2 2>/dev/null
pkill -9 -f nav2 2>/dev/null
echo "[hestia] feito."
