# config/ — parâmetros (os "botões" do Nav2 e da ronda)

Arquivos `.yaml` que os launch files carregam. Ficam separados do código para
poder ajustar sem recompilar.

| Arquivo             | Semana | O que é |
|---------------------|--------|---------|
| `nav2_params.yaml` ✅ | 3     | **PRONTO.** Parâmetros do Nav2 (AMCL, planner, controller, costmaps). Copiado de `turtlebot3_navigation2/param/humble/burger.yaml` — base testada para o `burger`. Ajustar aqui se precisar. |
| `waypoints.yaml`    | 3      | Pontos (x, y) da ronda de cuidado — a lista que o robô percorre patrulhando (a criar com o gerenciador de chamados). |

> O `nav2_params.yaml` veio do padrão do TurtleBot3 para Humble (não foi escrito
> do zero). Reinventar esse arquivo é um poço de tempo sem retorno de nota.
