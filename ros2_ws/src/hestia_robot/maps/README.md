# maps/ — mapa da casa (saída da Semana 2) ✅

**PRONTO.** Os dois arquivos já existem, gerados por SLAM (`slam_toolbox`) e salvos:

- `casa.pgm`  — a imagem do mapa (ocupação: preto=parede, branco=livre, cinza=fora).
- `casa.yaml` — os metadados (resolução 0.05 m/célula, origem) que apontam para o `.pgm`.

O mapeamento foi feito com o `launch/mapear.launch.py` (Gazebo + SLAM + Nav2) +
o explorador autônomo por fronteiras `scripts/explorador_nav2.py` dirigindo o
robô. Na Semana 3 o AMCL se localiza sobre este mapa. Para remapear (casa nova),
veja o comando abaixo.

Salva-se com:  `ros2 run nav2_map_server map_saver_cli -f ~/.../maps/casa`

A partir do momento em que estes dois existem, você NÃO depende mais do SLAM ao
vivo — o AMCL (Semana 3) se localiza sobre este mapa salvo. É o portão de saída
da Semana 2.
