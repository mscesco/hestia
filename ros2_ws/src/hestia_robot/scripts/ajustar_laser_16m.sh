#!/usr/bin/env bash
# ajustar_laser_16m.sh — estende o alcance do laser do TurtleBot3 burger de
# 3.5 m para 16 m no modelo do Gazebo.
#
# POR QUE: a casa do Blender (casa_blender.world) tem cômodos grandes (~8x8 m).
# Com o laser padrão de 3.5 m, no centro dos cômodos o robô quase não vê parede,
# e o AMCL (localização) diverge. Com 16 m ele enxerga as paredes opostas e
# localiza direito.
#
# RODAR UMA VEZ (dentro do WSL/Ubuntu, após instalar o turtlebot3_gazebo):
#   bash ajustar_laser_16m.sh
# Idempotente: se já estiver em 16 m, não faz nada. Guarda backup .bak.

set -e
SDF=/opt/ros/humble/share/turtlebot3_gazebo/models/turtlebot3_burger/model.sdf
if [ ! -f "$SDF" ]; then
  echo "ERRO: não achei $SDF — instale ros-humble-turtlebot3-gazebo primeiro."
  exit 1
fi
if grep -q "<max>16.0</max>" "$SDF"; then
  echo "[laser] já está em 16 m — nada a fazer."
  exit 0
fi
sudo cp -n "$SDF" "$SDF.bak"
sudo sed -i 's|<max>3.5</max>|<max>16.0</max>|' "$SDF"
echo "[laser] alcance ajustado para 16 m. Confirmação:"
grep -n "<max>" "$SDF" | head
