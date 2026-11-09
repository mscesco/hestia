#!/usr/bin/env bash
# Publica um chamado no tópico /chamados (transporte: std_msgs/String com JSON).
#
# Uso:  bash publica_chamado.sh <tipo> <PRIORIDADE> <x> <y>
# Ex.:  bash publica_chamado.sh agua  PEDIDO_COMUM  3.0 -1.0
#       bash publica_chamado.sh queda EMERGENCIA   -4.5 2.0
#
# PRIORIDADE: PATRULHA | PEDIDO_COMUM | EMERGENCIA
source /opt/ros/humble/setup.bash
TIPO="${1:?tipo}"; PRIO="${2:?prioridade}"; X="${3:?x}"; Y="${4:?y}"
JSON="{\"tipo\":\"$TIPO\",\"prioridade\":\"$PRIO\",\"x\":$X,\"y\":$Y}"
echo "publicando: $JSON"
ros2 topic pub -w 1 --times 1 /chamados std_msgs/msg/String "{data: '$JSON'}"
