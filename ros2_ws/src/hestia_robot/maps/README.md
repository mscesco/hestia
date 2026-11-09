# maps/ — mapa da casa (casa do Blender)

O mapa de ocupação que o Nav2 usa para localização e planejamento:

- `casa_blender.pgm` — a imagem do mapa (preto=parede, branco=livre, cinza=desconhecido).
- `casa_blender.yaml` — metadados (resolução 0.05 m/célula, origem `[-9.6, -3.6]`)
  que apontam para o `.pgm`.

Este mapa foi gerado **fatiando o mesh da casa do Blender**
(`worlds/casa_blender/casa_blender.obj`) na altura do laser, então já está
**alinhado** ao mundo do Gazebo (`casa_blender.world`) — escala 1, sem offset.
O AMCL (plano A) ou a TF estática (plano B) se localizam sobre ele.

Para gerar o mapa de uma casa nova com SLAM, salve com:
`ros2 run nav2_map_server map_saver_cli -f ~/.../maps/<nome>`
