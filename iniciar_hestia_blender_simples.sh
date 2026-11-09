#!/bin/bash
# =====================================================================
# iniciar_hestia_blender_simples.sh — PLANO B: sobe o Héstia na casa do
# Blender SEM AMCL (TF estática map->odom + odometria do Gazebo + ponte de
# pose). Localização "cravada" de simulação, para GARANTIR a demo.
#   wsl -d <sua-distro> bash /mnt/c/Users/Usuario/Documents/hestia/iniciar_hestia_blender_simples.sh
# Para derrubar: bash parar_hestia.sh
# =====================================================================
source /opt/ros/humble/setup.bash
WS="$(cd "$(dirname "$0")" && pwd)"
source "$WS/ros2_ws/install/setup.bash"
export TURTLEBOT3_MODEL=burger
grep -qi microsoft /proc/version 2>/dev/null && export LIBGL_ALWAYS_SOFTWARE=1
LOGDIR=/tmp/hestia_logs; mkdir -p "$LOGDIR"

echo "[hestia] limpando processos antigos..."
pkill -9 -f "uvicorn servidor:app" 2>/dev/null
pkill -9 -f "ros2 launch hestia_robot" 2>/dev/null
pkill -9 -f gzserver 2>/dev/null; pkill -9 -f gzclient 2>/dev/null
pkill -9 -f no_ponte 2>/dev/null; pkill -9 -f gerenciador_chamados 2>/dev/null
pkill -9 -f pose_tf_bridge 2>/dev/null
pkill -9 -f bringup 2>/dev/null; pkill -9 -f nav2 2>/dev/null
sleep 3

echo "[hestia] 1/4 subindo a ponte (FastAPI)..."
( cd "$WS/ponte" && setsid nohup python3 -m uvicorn servidor:app --host 0.0.0.0 --port 8000 >"$LOGDIR/ponte.log" 2>&1 < /dev/null & )

echo "[hestia] 2/4 subindo Gazebo(casa_blender) + TF estatica + map_server + Nav2 (SEM AMCL)..."
setsid nohup ros2 launch hestia_robot localizacao_blender_simples.launch.py >"$LOGDIR/localizacao.log" 2>&1 < /dev/null &

echo "[hestia] 3/4 aguardando Nav2 + pose (/pose_robo via tf) ficarem prontos..."
clock=0; nav=0; pose=0
for i in $(seq 1 60); do
  timeout 3 ros2 topic echo /clock --once >/dev/null 2>&1 && clock=1
  ros2 action list 2>/dev/null | grep -q navigate_to_pose && nav=1
  timeout 3 ros2 topic echo /pose_robo --once >/dev/null 2>&1 && pose=1
  [ "$clock" -eq 1 ] && [ "$nav" -eq 1 ] && [ "$pose" -eq 1 ] && break
  sleep 3
done
echo "[hestia] prontidao: clock=$clock nav=$nav pose=$pose"

echo "[hestia] 4/4 subindo no_ponte + gerenciador_chamados (ronda inicia sozinha)..."
setsid nohup ros2 run hestia_robot no_ponte --ros-args -p use_sim_time:=true -p pose_topic:=/pose_robo >"$LOGDIR/no_ponte.log" 2>&1 < /dev/null &
setsid nohup ros2 run hestia_robot gerenciador_chamados --ros-args -p use_sim_time:=true >"$LOGDIR/gerenciador.log" 2>&1 < /dev/null &
sleep 5

echo "[hestia] status da ponte:"
curl -s -m 3 http://localhost:8000/status; echo
echo "HESTIA_UP(simples) clock=$clock nav=$nav pose=$pose"
