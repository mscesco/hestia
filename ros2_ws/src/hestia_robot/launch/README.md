# launch/ — arquivos de bringup (o que sobe o sistema)

Um launch file liga vários nós de uma vez, com os parâmetros certos, num
comando só. Sem isso, cada teste vira 5 comandos manuais e a integração
vira um inferno.

**Casa do Blender (fluxo atual):**

| Arquivo | O que faz |
|---------|-----------|
| `localizacao_blender.launch.py` ⭐ | **PRINCIPAL.** Gazebo (`casa_blender.world`) + Nav2 + **AMCL** sobre `maps/casa_blender.yaml` + spawn em (0,6) + RViz (arg `rviz`, padrão on). |
| `localizacao_blender_simples.launch.py` 🛟 | **PLANO B (garante a demo).** Mesmo `bringup` do plano A (mapa chega ao planejador), mas com `nav2_params_simples.yaml` (**AMCL sem TF**, `tf_broadcast:false`) + **TF estática** `map->odom` (0,6) = localização exata da simulação + `pose_tf_bridge` publicando a pose real em `/pose_robo` (o `no_ponte` lê daí) + RViz. Use se o AMCL divergir. |

> A integração ponta a ponta (ponte + `no_ponte` + `gerenciador_chamados`) é
> subida pelos scripts da raiz `iniciar_hestia_blender.sh` (com AMCL) e
> `iniciar_hestia_blender_simples.sh` (plano B), não por um launch único.
>
> Para o ROS instalar esta pasta, ela já está declarada no `setup.py`
> (`data_files`). Após criar/editar arquivos aqui, rode `colcon build`.
