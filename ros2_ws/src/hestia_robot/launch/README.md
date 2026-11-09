# launch/ — arquivos de bringup (o que sobe o sistema)

Um launch file liga vários nós de uma vez, com os parâmetros certos, num
comando só. Sem isso, cada teste vira 5 comandos manuais e a integração
(Semana 7) vira um inferno. Ainda **vazio de propósito** — cada arquivo abaixo
é escrito na semana indicada.

| Arquivo                | Semana | O que faz |
|------------------------|--------|-----------|
| `slam.launch.py` ✅     | 2      | **PRONTO.** Sobe Gazebo (`turtlebot3_house`) + `slam_toolbox` + RViz para MAPEAR a casa. |
| `localizacao.launch.py` ✅ | 3   | **PRONTO.** Sobe Gazebo + Nav2 + AMCL sobre o `maps/casa.yaml` + RViz (malha fechada). |
| `sistema.launch.py`    | 7      | Tudo acima + `gerenciador_chamados` + `no_ponte` (integração ponta a ponta). |

> Para o ROS instalar esta pasta, ela já está declarada no `setup.py`
> (`data_files`). É só criar os arquivos aqui e rodar `colcon build`.
