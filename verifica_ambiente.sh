#!/usr/bin/env bash
# Verificador do ambiente da Semana 1 do NEXUS.
# Rode:  bash verifica_ambiente.sh
# Nao altera nada no sistema, so checa e reporta.

ok()   { echo -e "  [ OK ]  $1"; }
falha(){ echo -e "  [FALHA] $1"; FALHAS=$((FALHAS+1)); }
FALHAS=0

echo "=== Verificacao do ambiente NEXUS (Semana 1) ==="

# 1. Ubuntu 22.04
if grep -q "22.04" /etc/os-release 2>/dev/null; then
  ok "Ubuntu 22.04 detectado"
else
  falha "Nao e Ubuntu 22.04 (o ROS Humble exige 22.04)"
fi

# 2. ROS 2 disponivel no terminal
if command -v ros2 >/dev/null 2>&1; then
  ok "comando 'ros2' encontrado"
else
  falha "'ros2' nao encontrado — falta 'source /opt/ros/humble/setup.bash'?"
fi

# 3. Distro Humble
if [ "$ROS_DISTRO" = "humble" ]; then
  ok "ROS_DISTRO = humble"
else
  falha "ROS_DISTRO='$ROS_DISTRO' (esperado: humble)"
fi

# 4. Pacotes do projeto
if command -v ros2 >/dev/null 2>&1; then
  for pkg in nav2_bringup slam_toolbox turtlebot3_gazebo; do
    if ros2 pkg list 2>/dev/null | grep -qx "$pkg"; then
      ok "pacote '$pkg' instalado"
    else
      falha "pacote '$pkg' NAO instalado"
    fi
  done
fi

# 5. Modelo do TurtleBot3
if [ -n "$TURTLEBOT3_MODEL" ]; then
  ok "TURTLEBOT3_MODEL = $TURTLEBOT3_MODEL"
else
  falha "TURTLEBOT3_MODEL nao definido (ex.: export TURTLEBOT3_MODEL=burger)"
fi

# 6. nmap (usado no pentest, semana 6)
if command -v nmap >/dev/null 2>&1; then
  ok "nmap instalado"
else
  echo -e "  [aviso] nmap ausente (so sera necessario na Semana 6)"
fi

echo "------------------------------------------------"
if [ "$FALHAS" -eq 0 ]; then
  echo "  Tudo certo. Agora rode o portao de saida:"
  echo "  ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py"
else
  echo "  $FALHAS item(ns) com falha. Reveja o INSTALL_WSL2.md."
fi
