#!/bin/bash
# =====================================================================
# iniciar_hestia_blender.sh — sobe o sistema Héstia na CASA DO BLENDER (com AMCL).
# Usa localizacao_blender.launch.py (mundo casa_blender.world + mapa
# casa_blender.yaml) e pose inicial (0,6).
#   wsl -d Ubuntu-22.04 -u root bash /mnt/c/.../hestia/iniciar_hestia_blender.sh
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
pkill -9 -f bringup 2>/dev/null; pkill -9 -f nav2 2>/dev/null
sleep 3

echo "[hestia] 1/5 subindo a ponte (FastAPI)..."
( cd "$WS/ponte" && setsid nohup python3 -m uvicorn servidor:app --host 0.0.0.0 --port 8000 >"$LOGDIR/ponte.log" 2>&1 < /dev/null & )

echo "[hestia] 2/5 subindo Gazebo(casa_blender) + AMCL + Nav2..."
setsid nohup ros2 launch hestia_robot localizacao_blender.launch.py >"$LOGDIR/localizacao.log" 2>&1 < /dev/null &

echo "[hestia] 3/5 aguardando AMCL + Nav2 ficarem prontos..."
# Checagem por lista de nós/ações (confiável no WSL). NÃO usar `ros2 topic echo
# /clock --once`: no WSL ele costuma pendurar e nunca marcar pronto, travando o
# script mesmo com tudo no ar.
amcl=0; nav=0
for i in $(seq 1 40); do
  ros2 node list 2>/dev/null | grep -q '/amcl' && amcl=1
  ros2 action list 2>/dev/null | grep -q navigate_to_pose && nav=1
  [ "$amcl" -eq 1 ] && [ "$nav" -eq 1 ] && break
  sleep 3
done
echo "[hestia] prontidao: amcl=$amcl nav=$nav"

echo "[hestia] 4/5 publicando pose inicial do AMCL em (0,6)..."
# publica algumas vezes p/ garantir que o AMCL recebe (robo spawna em 0,6)
timeout 8 ros2 topic pub -r 3 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 6.0, z: 0.0}, orientation: {z: 0.0, w: 1.0}}, covariance: [0.25,0,0,0,0,0, 0,0.25,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0.0685]}}" >/dev/null 2>&1
sleep 3

echo "[hestia] 5/5 subindo no_ponte + gerenciador_chamados + no_percepcao (ronda inicia sozinha)..."
setsid nohup ros2 run hestia_robot no_ponte --ros-args -p use_sim_time:=true >"$LOGDIR/no_ponte.log" 2>&1 < /dev/null &
setsid nohup ros2 run hestia_robot gerenciador_chamados --ros-args -p use_sim_time:=true >"$LOGDIR/gerenciador.log" 2>&1 < /dev/null &
setsid nohup ros2 run hestia_robot no_percepcao --ros-args -p use_sim_time:=true >"$LOGDIR/no_percepcao.log" 2>&1 < /dev/null &
sleep 5

echo "[hestia] status da ponte:"
curl -s -m 3 http://localhost:8000/status; echo
echo "HESTIA_UP amcl=$amcl nav=$nav"
