#!/bin/bash
# =====================================================================
# iniciar_hestia.sh — sobe o sistema Héstia inteiro dentro do WSL.
#
# Uso (no PowerShell do Windows):
#   wsl -d Ubuntu-22.04 -u lauri bash /mnt/c/Users/lauri/Downloads/hestia/iniciar_hestia.sh
#
# Sobe, em ordem: ponte FastAPI -> Gazebo+AMCL+Nav2 -> publica pose inicial
# -> no_ponte -> gerenciador_chamados (que inicia a ronda sozinho).
# Os processos ficam DESACOPLADOS (setsid/nohup): sobrevivem ao fechamento
# do terminal. Logs em /tmp/hestia_logs/. Depois, abra o Godot e dê Play.
# Para derrubar tudo: bash parar_hestia.sh (ou wsl --terminate Ubuntu-22.04).
# =====================================================================
source /opt/ros/humble/setup.bash
# raiz do projeto = pasta deste script (portável: funciona em qualquer
# máquina/usuário, seja WSL em /mnt/c/... ou Linux nativo em ~/hestia).
WS="$(cd "$(dirname "$0")" && pwd)"
source "$WS/ros2_ws/install/setup.bash"
export TURTLEBOT3_MODEL=burger
# render por software só no WSL; no Linux nativo deixa o Gazebo usar a GPU.
grep -qi microsoft /proc/version 2>/dev/null && export LIBGL_ALWAYS_SOFTWARE=1
LOGDIR=/tmp/hestia_logs; mkdir -p "$LOGDIR"

echo "[hestia] limpando processos antigos..."
pkill -9 -f "uvicorn servidor:app" 2>/dev/null
pkill -9 -f "ros2 launch hestia_robot" 2>/dev/null
pkill -9 -f gzserver 2>/dev/null
pkill -9 -f gzclient 2>/dev/null
pkill -9 -f no_ponte 2>/dev/null
pkill -9 -f gerenciador_chamados 2>/dev/null
pkill -9 -f explorador_nav2 2>/dev/null
sleep 2

echo "[hestia] 1/5 subindo a ponte (FastAPI)..."
( cd "$WS/ponte" && setsid nohup python3 -m uvicorn servidor:app --host 0.0.0.0 --port 8000 >"$LOGDIR/ponte.log" 2>&1 < /dev/null & )

echo "[hestia] 2/5 subindo Gazebo + AMCL + Nav2 (pode levar 1-3 min)..."
setsid nohup ros2 launch hestia_robot localizacao.launch.py >"$LOGDIR/localizacao.log" 2>&1 < /dev/null &

echo "[hestia] 3/5 aguardando AMCL + Nav2 ficarem prontos..."
clock=0; amcl=0; nav=0
for i in $(seq 1 90); do
  timeout 3 ros2 topic echo /clock --once >/dev/null 2>&1 && clock=1
  ros2 node list 2>/dev/null | grep -q '/amcl' && amcl=1
  ros2 action list 2>/dev/null | grep -q navigate_to_pose && nav=1
  [ "$clock" -eq 1 ] && [ "$amcl" -eq 1 ] && [ "$nav" -eq 1 ] && break
  sleep 3
done
echo "[hestia] prontidao: clock=$clock amcl=$amcl nav=$nav"

echo "[hestia] 4/5 enxugando janelas pesadas e publicando pose inicial do AMCL..."
pkill -9 -f /rviz2 2>/dev/null
pkill -9 -f gzclient 2>/dev/null
timeout 5 ros2 topic pub -r 2 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: map}, pose: {pose: {position: {x: 1.96, y: -1.52, z: 0.0}, orientation: {z: 0.0, w: 1.0}}, covariance: [0.25,0.0,0.0,0.0,0.0,0.0, 0.0,0.25,0.0,0.0,0.0,0.0, 0.0,0.0,0.0,0.0,0.0,0.0, 0.0,0.0,0.0,0.0,0.0,0.0, 0.0,0.0,0.0,0.0,0.0,0.0, 0.0,0.0,0.0,0.0,0.0,0.0685]}}" >/dev/null 2>&1
sleep 3

echo "[hestia] 5/5 subindo no_ponte + gerenciador_chamados (ronda inicia sozinha)..."
setsid nohup ros2 run hestia_robot no_ponte --ros-args -p use_sim_time:=true >"$LOGDIR/no_ponte.log" 2>&1 < /dev/null &
setsid nohup ros2 run hestia_robot gerenciador_chamados --ros-args -p use_sim_time:=true >"$LOGDIR/gerenciador.log" 2>&1 < /dev/null &
sleep 4

echo "[hestia] status da ponte:"
curl -s -m 3 http://localhost:8000/status; echo
echo "HESTIA_UP clock=$clock amcl=$amcl nav=$nav"
